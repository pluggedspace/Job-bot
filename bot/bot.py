import logging
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from django.conf import settings
from asgiref.sync import sync_to_async
from bot.models import User, Job, Alert
from bot.utils import get_jobs, create_paystack_payment, verify_paystack_payment
from bot.decorators import subscription_required
from telegram.constants import ParseMode
from telegram.constants import UpdateType

import threading
import asyncio


logger = logging.getLogger(__name__)

# Global constants
FREE_SEARCH_LIMIT = 5

class JobSearchBot:
    def __init__(self):
        self.application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
        self.setup_handlers()
        self.job_cache = {}

    def setup_handlers(self):
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("findjobs", self.find_jobs))
        self.application.add_handler(CommandHandler("subscribe", self.subscribe))
        self.application.add_handler(CommandHandler("setalert", self.set_alert))
        self.application.add_handler(CommandHandler("quota", self.check_quota))
        self.application.add_handler(CommandHandler("manual_verify", self.manual_verify))
        self.application.add_handler(CommandHandler("history", self.history))
        
        # Callback handlers
        self.application.add_handler(CallbackQueryHandler(self.verify_payment, pattern=r"^verify_"))
        self.application.add_handler(CallbackQueryHandler(self.show_job_details, pattern=r"^view_")) 
        self.application.add_handler(CallbackQueryHandler(self.back_to_results, pattern=r"^back_to_results$"))

    # Database helper methods
    @staticmethod
    @sync_to_async
    def get_user(user_id):
        try:
            return User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            return None

    @staticmethod
    @sync_to_async
    def create_user(user_id, username):
        return User.objects.get_or_create(
            user_id=user_id,
            defaults={'username': username}
        )

    @staticmethod
    @sync_to_async
    def save_job(user_id, job_id, title, company):
        user = User.objects.get(user_id=user_id)
        return Job.objects.create(
            user=user,
            job_id=job_id,
            title=title,
            company=company
        )

    @staticmethod
    @sync_to_async
    def get_user_jobs(user_id, limit=10):
        return list(Job.objects.filter(user__user_id=user_id).order_by('-saved_at')[:limit])

    @staticmethod
    @sync_to_async
    def create_alert(user_id, query):
        user = User.objects.get(user_id=user_id)
        return Alert.objects.create(user=user, query=query)

    @staticmethod
    @sync_to_async
    def update_user_status(user_id, status, reference=None):
        user = User.objects.get(user_id=user_id)
        user.subscription_status = status
        if reference:
            user.payment_reference = reference
        user.save()
        return user

    @staticmethod
    @sync_to_async
    def increment_search_count(user_id):
        user = User.objects.get(user_id=user_id)
        user.search_count += 1
        user.save()
        return user

    @staticmethod
    @sync_to_async
    def get_alerts():
        return list(Alert.objects.filter(active=True))

    # Command handlers
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        username = update.effective_user.username
        
        user, created = await self.create_user(user_id, username)
        
        if not created:
            user.username = username
            await sync_to_async(user.save)()
        
        await update.message.reply_text(
            "Welcome to the Job Search Bot!\n\n"
            "Use /findjobs to search jobs, /subscribe to upgrade, /setalert to create job alerts, "
            "/quota to check your limit, and /history to view your saved jobs."
        )

    async def show_job_details(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()  # Acknowledge the callback
        
        job_id = query.data.split("_", 1)[1]
        job = self.job_cache.get(job_id)
        
        if not job:
            await query.edit_message_text("Job details no longer available.")
            return
        
        # Format the job details
        message = (
            f"<b>{job.get('job_title', 'N/A')}</b>\n"
            f"<b>Company:</b> {job.get('employer_name', 'Unknown')}\n"
            f"<b>Location:</b> {job.get('job_city', 'N/A')}, {job.get('job_country', 'N/A')}\n"
            f"<b>Type:</b> {job.get('job_employment_type', 'N/A')}\n"
            f"<b>Posted:</b> {job.get('job_posted_at', 'N/A')}\n\n"
        )
        
        # Add job description if available (trim if too long)
        description = job.get('job_description', '')
        if description:
            if len(description) > 1000:
                description = description[:1000] + "..."
            message += f"<b>Description:</b>\n{description}\n\n"
        
        # Add apply link if available
        apply_url = job.get('job_apply_link')
        buttons = []
        if apply_url:
            buttons.append([InlineKeyboardButton("Apply Now", url=apply_url)])
        
        # Add back button
        buttons.append([InlineKeyboardButton("Back to Results", callback_data="back_to_results")])
        
        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.HTML
        )

    async def find_jobs(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        if not context.args:
            await update.message.reply_text("Please provide search keywords.")
            return
        
        query = " ".join(context.args)
        
        user = await self.get_user(user_id)
        if not user:
            await update.message.reply_text("Please register first with /start")
            return
        
        is_premium = user.subscription_status == 'Paid'
        
        if not is_premium:
            if user.search_count >= FREE_SEARCH_LIMIT:
                await update.message.reply_text("Free search limit reached. Use /subscribe to upgrade.")
                return
            await self.increment_search_count(user_id)
        
        jobs = get_jobs(query)
        if not jobs:
            await update.message.reply_text("No jobs found for your search criteria.")
            return
        
        # Cache the jobs for details view
        for job in jobs:
            job_id = job.get("job_id", str(hash(job.get('job_title', '') + job.get('employer_name', ''))))
            self.job_cache[job_id] = job
        
        # Send the first 5 jobs with details buttons
        for job in jobs[:5]:
            title = job.get('job_title', 'N/A')
            company = job.get('employer_name', 'Unknown')
            job_id = job.get("job_id", str(hash(title + company)))
            
            await self.save_job(user_id, job_id, title, company)
            
            keyboard = [[InlineKeyboardButton("View Details", callback_data=f"view_{job_id}")]]
            await update.message.reply_text(
                f"{title} at {company}",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

    async def back_to_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
    
        # Retrieve the original message (you'd need to store this message_id somewhere)
        original_message_id = context.user_data.get('results_message_id')
        if original_message_id:
            try:
                await context.bot.edit_message_text(
                    chat_id=query.message.chat_id,
                    message_id=original_message_id,
                    text="Here are your job results:",
                    reply_markup=...  # Original keyboard markup
                )
                await query.message.delete()
            except Exception as e:
                logger.error(f"Error returning to results: {e}")
                await query.edit_message_text("Could not return to original results. Please perform a new search.")
        else:
            await query.edit_message_text("Session expired. Please perform a new search with /findjobs")

    async def subscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        if not context.args:
            await update.message.reply_text("Please provide your email. Usage: /subscribe your_email@example.com")
            return
        
        email = context.args[0]
        reference = f"REF_{user_id}{int(time.time())}"
        
        user = await self.get_user(user_id)
        if not user:
            await update.message.reply_text("Please register first with /start")
            return
        
        data = create_paystack_payment(email, 750, reference)
        
        if not data.get("status"):
            await update.message.reply_text("Error creating payment link.")
            return
        
        url = data['data']['authorization_url']
        await self.update_user_status(user_id, "Pending", reference)
        
        buttons = [
            [InlineKeyboardButton("Pay Now", url=url)],
            [InlineKeyboardButton("Verify", callback_data=f"verify_{reference}")]
        ]
        await update.message.reply_text(
            "Complete your payment:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    async def verify_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        ref = query.data.split("_", 1)[1]
        user_id = str(update.effective_user.id)
        
        try:
            result = verify_paystack_payment(ref)
            if result.get("data", {}).get("status") == "success":
                await self.update_user_status(user_id, "Paid", ref)
                await query.edit_message_text("Payment verified. You are now a premium user.")
            else:
                await query.edit_message_text("Verification failed. Please try again later.")
        except Exception as e:
            logger.error(f"Payment verification error: {e}")
            await query.edit_message_text("An error occurred during verification.")

    @subscription_required
    async def set_alert(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        if not context.args:
            await update.message.reply_text("Usage: /setalert keyword(s)")
            return
        
        query = " ".join(context.args)
        
        user = await self.get_user(user_id)
        if not user:
            await update.message.reply_text("Please register first with /start")
            return
        
        alert = await self.create_alert(user_id, query)
        await update.message.reply_text(f"Alert set for '{query}' (ID: {alert.id})")

    async def check_quota(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        user = await self.get_user(user_id)
        if not user:
            await update.message.reply_text("Please register first with /start")
            return
        
        if user.subscription_status == 'Paid':
            await update.message.reply_text("You have unlimited access as a premium user.")
            return
        
        remaining = max(0, FREE_SEARCH_LIMIT - user.search_count)
        await update.message.reply_text(f"You have {remaining} free searches remaining today.")

    async def history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        jobs = await self.get_user_jobs(user_id)
        
        if not jobs:
            await update.message.reply_text("You haven't saved any jobs yet.")
            return
        
        message = "Your recent saved jobs:\n\n"
        for job in jobs:
            message += f"{job.title} at {job.company}\n"
        
        await update.message.reply_text(message)

    async def manual_verify(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        if not context.args:
            await update.message.reply_text("Usage: /manual_verify PAYMENT_REFERENCE")
            return
        
        ref = context.args[0]
        
        user = await self.get_user(user_id)
        if not user:
            await update.message.reply_text("Please register first with /start")
            return
        
        try:
            result = verify_paystack_payment(ref)
            if result.get("data", {}).get("status") == "success":
                await self.update_user_status(user_id, "Paid", ref)
                await update.message.reply_text("Payment verified successfully. You are now a premium user.")
            else:
                await update.message.reply_text("Verification failed or still pending. Please try again later.")
        except Exception as e:
            logger.error(f"Manual verification error: {e}")
            await update.message.reply_text("An error occurred during verification.")

    

    def run(self):
        self.application.run_polling()
        





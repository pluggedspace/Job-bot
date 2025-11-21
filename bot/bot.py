import logging
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)
from django.conf import settings
from asgiref.sync import sync_to_async
from bot.models import User, Job, Alert, InterviewSession, InterviewResponse
from bot.utils import get_jobs, create_paystack_payment, verify_paystack_payment, get_jobs_arbeitnow
from bot.decorators import subscription_required
from telegram.constants import ParseMode
from telegram.constants import UpdateType
from bot.cv_builder import get_cv_handler
from django.db import transaction
import asyncio
from bot.services.career_path import get_career_path_data, resolve_career_path
from bot.services.upskill import get_upskill_plan
from bot.improve import generate_cover_letter, review_cv
from bot.services.interview import handle_interview_practice

logger = logging.getLogger(__name__)

# Global constants
FREE_SEARCH_LIMIT = 10

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
        self.application.add_handler(CommandHandler("myalerts", self.my_alerts))
        self.application.add_handler(CommandHandler("quota", self.check_quota))
        self.application.add_handler(CommandHandler("manual_verify", self.manual_verify))
        self.application.add_handler(CommandHandler("history", self.history))
        self.application.add_handler(CommandHandler("careerpath", self.careerpath_command))
        self.application.add_handler(CommandHandler("upskill", self.upskill_command))
        self.application.add_handler(get_cv_handler())
        self.application.add_handler(CommandHandler("view_cv", self.view_cv))
        self.application.add_handler(CommandHandler("coverletter", self.coverletter_handler))
        self.application.add_handler(CommandHandler("cv_review", self.cv_review_handler))
        self.application.add_handler(CommandHandler("practice", self.interview_practice_handler))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.interview_practice_handler))

        # Callback handlers
        self.application.add_handler(CallbackQueryHandler(self.verify_payment, pattern=r"^verify_"))
        self.application.add_handler(CallbackQueryHandler(self.show_job_details, pattern=r"^view_")) 
        self.application.add_handler(CallbackQueryHandler(self.back_to_results, pattern=r"^back_to_results$"))
        self.application.add_handler(CallbackQueryHandler(self.toggle_alert, pattern=r"^alert_"))

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
        
    @sync_to_async
    def get_user_or_create(self, telegram_user):
        user, _ = User.objects.get_or_create(
            user_id=telegram_user.id,
            defaults={
                "username": telegram_user.username or "",
            }
        )
        return user
        
    async def cv_review_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = await self.get_user_or_create(update.effective_user)

        await update.message.reply_text("🔍 Reviewing your CV, one moment...")

        result = await asyncio.to_thread(review_cv, user)

        if result["error"]:
            await update.message.reply_text(
                f"⚠️ Missing profile fields: {', '.join(result['missing_fields'])}\n"
                f"Use /cv_builder to complete your profile."
            )
        else:
            await update.message.reply_text(
                f"📋 *CV Review Report:*\n\n{result['cv_review']}",
                parse_mode=ParseMode.MARKDOWN
            )

    async def coverletter_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = await self.get_user_or_create(update.effective_user)
        message = update.message.text

        # Parse: /coverletter Job Title | Company
        try:
            parts = message.replace("/coverletter", "").strip().split("|")
            job_title = parts[0].strip()
            company = parts[1].strip() if len(parts) > 1 else None
        except Exception:
            await update.message.reply_text("❗ Usage: `/coverletter Job Title | Company Name`", parse_mode=ParseMode.MARKDOWN)
            return

        # Generate the letter
        await update.message.reply_text("🧠 Generating your cover letter, please wait...")

        result = await asyncio.to_thread(generate_cover_letter, user, job_title, company)

        if result["error"]:
            await update.message.reply_text(
                f"⚠️ Missing profile fields: {', '.join(result['missing_fields'])}\n"
                f"Use /cv_builder to complete your profile."
            )
        else:
            await update.message.reply_text(
                f"📄 *Cover Letter for {job_title} at {company or 'Company'}*\n\n"
                f"{result['cover_letter']}",
                parse_mode=ParseMode.MARKDOWN
            )

    async def interview_practice_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = await self.get_user_or_create(update.effective_user)
        user_input = update.message.text.strip()

        # If the message starts with /practice, treat as a start
        is_start = user_input.lower().startswith("/practice")

        # Send thinking/loading message
        if is_start:
            await update.message.reply_text("🎤 Starting your mock interview... Get ready!")
        else:
            await update.message.reply_text("✍️ Got it! Evaluating your response...")

        # Call the handler in thread to avoid blocking
        result = await handle_interview_practice(user, None if is_start else user_input)

        await update.message.reply_text(result)
    
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
        """Guaranteed to save alerts to database"""
        try:
            with transaction.atomic():
                user = User.objects.get(user_id=user_id)
                alert = Alert.objects.create(
                    user=user,
                    query=query,
                    active=True
                )
                logger.info(f"ALERT SAVED - ID: {alert.id}")
                return alert
        except User.DoesNotExist:
            logger.error(f"USER NOT FOUND: {user_id}")
            return None
        except Exception as e:
            logger.error(f"ALERT SAVE FAILED: {str(e)}", exc_info=True)
            return None

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

    @staticmethod
    @sync_to_async
    def get_user_alerts(user_id):
        return list(Alert.objects.filter(user__user_id=user_id).order_by('-created_at'))

    @staticmethod
    @sync_to_async
    def toggle_alert_status(alert_id):
        try:
            alert = Alert.objects.get(id=alert_id)
            alert.active = not alert.active
            alert.save()
            return alert
        except Alert.DoesNotExist:
            return None

    # Command handlers
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        username = update.effective_user.username
        
        user, created = await self.create_user(user_id, username)
        
        if not created:
            user.username = username
            await sync_to_async(user.save)()
        
        await update.message.reply_text(
            "👋 Welcome to the Job Search Bot!\n\n"
            "🔍 <b>Search Jobs</b>\n"
            "Use /findjobs to search for jobs\n"
            "Example: /findjobs python developer remote\n\n"
            "📝 <b>Build Your CV</b>\n"
            "Use /build_cv to create a professional CV\n"
            "Use /view_cv to view CV\n\n"
            "🔔 <b>Job Alerts</b>\n"
            "Use /setalert to create job alerts\n"
            "Use /myalerts to manage your alerts\n\n"
            "📊 <b>Career Development</b>\n"
            "• /careerpath - Explore career progression\n"
            "• /practice - Interview practice\n"
            "• /upskill - Get personalized learning plan\n\n"
            "✍️ <b>Application Tools</b>\n"
            "• /coverletter Job Title | Company – Generate a tailored cover letter\n"
            "• /cv_review – Get suggestions to improve your CV\n\n"
            "💎 <b>Premium Features</b>\n"
            "• Unlimited job searches\n"
            "• Up to 5 active job alerts\n"
            "• View all search results\n"
            "Use /subscribe to upgrade\n\n"
            "📊 <b>Other Commands</b>\n"
            "• /quota - Check your search limit\n"
            "• /history - View saved jobs\n\n"
            f"Free users get {FREE_SEARCH_LIMIT} searches per month.",
            parse_mode=ParseMode.HTML
        )

    async def upskill_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user

        try:
            user_obj = await sync_to_async(User.objects.get)(user_id=str(user.id))
        except User.DoesNotExist:
            await update.message.reply_text("User not found. Please register with /start first.")
            return

        user_input = " ".join(context.args) if context.args else None
        plan = await sync_to_async(get_upskill_plan)(user_obj, user_input)

        if not plan or not plan.get('target'):
            await update.message.reply_text(
                "⚠️ Could not generate an upskill plan. Please specify a job title or skill like:\n\n`/upskill software engineer`",
                parse_mode='Markdown'
            )
            return

        msg = f"📚 *Upskill Plan for* `{plan['target']}`\n\n"

        if not plan['skills_to_gain']:
            msg += "❌ Could not generate a skill path or resources.\n"
            msg += f"_Note: {plan.get('note', 'Try again later or check your role input.')}_"
        else:
            msg += "*Skills to gain:*\n"
            for skill in plan['skills_to_gain']:
                skill_name = skill.get('name')
                course = skill.get('course', {})
                course_title = course.get('title', 'Free course')
                course_url = course.get('url', '#')
                msg += f"• *{skill_name}* — [{course_title}]({course_url})\n"

            msg += f"\nℹ️ _{plan.get('note', '')}_"

        await update.message.reply_markdown(msg, disable_web_page_preview=True)

    async def careerpath_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_input = ' '.join(context.args) if context.args else None
        try:
            user = await sync_to_async(User.objects.get)(user_id=str(update.effective_user.id))
        except User.DoesNotExist:
            await update.message.reply_text("User not found. Please register with /start first.")
            return

        if not user_input and not hasattr(user, 'profile'):
            await update.message.reply_text("❌ Could not fetch career path. Please provide a job title or create your CV first.")
            return

        data, source = await sync_to_async(resolve_career_path)(user_input or user.profile.current_job_title)

        if "error" in data:
            await update.message.reply_text(f"❌ {data['error']}")
            return

        msg = f"📈 *Career Path for* `{data['input_title']}` (via {source})\n\n"
        msg += f"*Broader Roles:* {', '.join(data.get('broader', []) or ['N/A'])}\n"
        msg += f"*Narrower Roles:* {', '.join(data.get('narrower', []) or ['N/A'])}\n"
        msg += f"*Related:* {', '.join(data.get('related', []) or ['N/A'])}"

        await update.message.reply_text(msg, parse_mode="Markdown")

    async def show_job_details(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        job_id = query.data.split("_", 1)[1]
        job = self.job_cache.get(job_id)
        
        if not job:
            await query.edit_message_text("Job details no longer available.")
            return
        
        message = (
            f"<b>{job.get('job_title', 'N/A')}</b>\n"
            f"<b>Company:</b> {job.get('employer_name', 'Unknown')}\n"
            f"<b>Location:</b> {job.get('job_city', 'N/A')}, {job.get('job_country', 'N/A')}\n"
            f"<b>Type:</b> {job.get('job_employment_type', 'N/A')}\n"
            f"<b>Posted:</b> {job.get('job_posted_at', 'N/A')}\n\n"
        )
        
        description = job.get('job_description', '')
        if description:
            if len(description) > 1000:
                description = description[:1000] + "..."
            message += f"<b>Description:</b>\n{description}\n\n"
        
        apply_url = job.get('job_apply_link')
        buttons = []
        if apply_url:
            buttons.append([InlineKeyboardButton("Apply Now", url=apply_url)])
        
        buttons.append([InlineKeyboardButton("Back to Results", callback_data="back_to_results")])
        
        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.HTML
        )

    async def find_jobs(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        if not context.args:
            await update.message.reply_text(
                "Please provide search keywords.\n\n"
                "You can also use filters:\n"
                "- /findjobs python remote\n"
                "- /findjobs developer full-time\n"
                "- /findjobs marketing entry-level"
            )
            return
        
        query = " ".join(context.args)
        
        user = await self.get_user(user_id)
        if not user:
            await update.message.reply_text("Please register first with /start")
            return
        
        is_premium = user.subscription_status == 'Paid'
        
        if not is_premium:
            if user.search_count >= FREE_SEARCH_LIMIT:
                await update.message.reply_text(
                    f"You've reached your monthly limit of {FREE_SEARCH_LIMIT} free searches.\n"
                    "Use /subscribe to upgrade to premium for unlimited searches!"
                )
                return
            await self.increment_search_count(user_id)
        
        filters = {}
        if "remote" in query.lower():
            filters["remote"] = True
        if "full-time" in query.lower():
            filters["job_employment_type"] = "FULLTIME"
        if "part-time" in query.lower():
            filters["job_employment_type"] = "PARTTIME"
        if "entry-level" in query.lower():
            filters["job_experience_level"] = "ENTRY_LEVEL"
        
        jobs = get_all_jobs(query, filters)
        if not jobs:
            await update.message.reply_text(
                "No jobs found for your search criteria.\n\n"
                "Try:\n"
                "- Using different keywords\n"
                "- Removing filters\n"
                "- Checking your spelling"
            )
            return
        
        for job in jobs:
            job_id = job.get("job_id", str(hash(job.get('job_title', '') + job.get('employer_name', ''))))
            self.job_cache[job_id] = job
        
        message = f"Found {len(jobs)} jobs matching your search:\n\n"
        await update.message.reply_text(message)
        
        for job in jobs[:5]:
            title = job.get('job_title', 'N/A')
            company = job.get('employer_name', 'Unknown')
            location = f"{job.get('job_city', 'N/A')}, {job.get('job_country', 'N/A')}"
            job_type = job.get('job_employment_type', 'N/A')
            job_id = job.get("job_id", str(hash(title + company)))
            
            await self.save_job(user_id, job_id, title, company)
            
            keyboard = [[InlineKeyboardButton("View Details", callback_data=f"view_{job_id}")]]
            await update.message.reply_text(
                f"<b>{title}</b>\n"
                f"Company: {company}\n"
                f"Location: {location}\n"
                f"Type: {job_type}",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.HTML
            )
        
        if len(jobs) > 5:
            await update.message.reply_text(
                f"Showing first 5 results. Upgrade to premium to see all {len(jobs)} jobs!"
            )

    async def back_to_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
    
        original_message_id = context.user_data.get('results_message_id')
        if original_message_id:
            try:
                await context.bot.edit_message_text(
                    chat_id=query.message.chat_id,
                    message_id=original_message_id,
                    text="Here are your job results:",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("View Details", callback_data="view_1")]])
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
        await query.answer()
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

    async def set_alert(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Fixed version that guarantees alert saving"""
        user_id = str(update.effective_user.id)
        logger.info(f"SET ALERT STARTED for {user_id}")

        # Input validation
        if not context.args:
            await update.message.reply_text("Usage: /setalert keyword")
            return

        query = " ".join(context.args).strip()
        if len(query) < 2:
            await update.message.reply_text("Query too short")
            return

        try:
            # 1. Verify user exists
            user = await self.get_user(user_id)
            if not user:
                raise ValueError("User not registered")

            # 2. Check for duplicates
            duplicate = await sync_to_async(
                Alert.objects.filter(user=user, query=query).exists
            )()
            if duplicate:
                await update.message.reply_text("❌ You already have this alert!")
                return

            # 3. Check alert limit
            active_count = await sync_to_async(
                Alert.objects.filter(user=user, active=True).count
            )()
            if active_count >= 5:
                await update.message.reply_text("❌ Max 5 alerts allowed")
                return

            # 4. Create and verify alert
            alert = await self.create_alert(user_id, query)
            if not alert:
                raise ValueError("Alert creation returned None")

            # SUCCESS - send confirmation
            await update.message.reply_text(
                f"✅ Alert saved successfully!\n\n"
                f"ID: {alert.id}\n"
                f"Query: {query}\n\n"
                "You'll be notified of new matching jobs."
            )
            logger.info(f"ALERT CONFIRMED SAVED: {alert.id}")

        except Exception as e:
            logger.error(f"ALERT FAILURE: {str(e)}", exc_info=True)
            await update.message.reply_text(
                "⚠️ Failed to save alert. Our team has been notified.\n"
                "Please try again later."
            )

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
        message = "<b>Your recent saved jobs:</b>\n\n"
        for idx, job in enumerate(jobs, 1):
            if hasattr(job, 'job_apply_link') and job.job_apply_link:
                message += f"{idx}. <a href=\"{job.job_apply_link}\">{job.title}</a> at {job.company}\n"
            elif hasattr(job, 'url') and job.url:
                message += f"{idx}. <a href=\"{job.url}\">{job.title}</a> at {job.company}\n"
            else:
                message += f"{idx}. {job.title} at {job.company}\n"
        await update.message.reply_text(message, parse_mode=ParseMode.HTML)

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
            
    async def view_cv(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.message is None:
            return

        telegram_user_id = str(update.effective_user.id)

        try:
            user = await sync_to_async(User.objects.get)(user_id=telegram_user_id)
        except User.DoesNotExist:
            await update.message.reply_text("You don't have a profile yet. Use /cv to create your CV.")
            return

        if not user.cv_data:
            await update.message.reply_text("No CV found. Use /cv to create one.")
            return

        d = user.cv_data
        skills = ', '.join(user.skills or d.get('skills', []))
        education = "\n".join(f"- {e}" for e in d.get("education", []))
        experience = "\n".join(f"- {e}" for e in d.get("experience", []))

        message = (
            f"🧾 *Your CV Info*\n\n"
            f"*Name:* {d.get('name')}\n"
            f"*Title:* {d.get('title')}\n"
            f"*Email:* {d.get('email')}\n"
            f"*Phone:* {d.get('phone')}\n"
            f"*Summary:* {d.get('summary')}\n\n"
            f"*Skills:* {skills or 'N/A'}\n\n"
            f"*Education:*\n{education or 'N/A'}\n\n"
            f"*Experience:*\n{experience or 'N/A'}"
        )

        await update.message.reply_markdown(message)

    async def my_alerts(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        user = await self.get_user(user_id)
        if not user:
            await update.message.reply_text("Please register first with /start")
            return
    
        alerts = await self.get_user_alerts(user_id)
        if not alerts:
            await update.message.reply_text(
                "You don't have any job alerts set up.\n\n"
                "Use /setalert to create your first alert!"
            )
            return
    
        message = "Your Job Alerts:\n\n"
        for alert in alerts:
            status = "✅ Active" if alert.active else "❌ Inactive"
            message += (
                f"ID: {alert.id}\n"
                f"Query: {alert.query}\n"
                f"Status: {status}\n"
                f"Created: {alert.created_at.strftime('%Y-%m-%d')}\n\n"
            )
    
        keyboard = [
            [InlineKeyboardButton(
                f"{'Deactivate' if alert.active else 'Activate'} Alert {alert.id}",
                callback_data=f"alert_{alert.id}"
            )]
            for alert in alerts
        ]
    
        await update.message.reply_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    async def toggle_alert(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        alert_id = query.data.split("_", 1)[1]
        alert = await self.toggle_alert_status(alert_id)
        
        if not alert:
            await query.edit_message_text("Alert not found.")
            return
        
        status = "activated" if alert.active else "deactivated"
        await query.edit_message_text(
            f"Alert for '{alert.query}' has been {status}.\n\n"
            "Use /myalerts to manage your alerts."
        )

    def run(self):
        self.application.run_polling()

def get_all_jobs(query: str, filters: dict = None) -> list:
    jobs = []
    jobs += get_jobs(query, filters)
    jobs += get_jobs_arbeitnow(query, filters)
    return jobs
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
from bot.utils import (
    create_paystack_payment, verify_paystack_payment,
    create_flutterwave_payment, verify_flutterwave_payment
)
from bot.decorators import subscription_required
from bot.functions.jobs import get_jobs, get_jobs_arbeitnow, get_all_jobs
from telegram.constants import ParseMode
from telegram.constants import UpdateType
from bot.cv_builder import get_cv_handler
from django.db import transaction
import asyncio
from bot.services.career_path import get_career_path_data, resolve_career_path
from bot.services.upskill import get_upskill_plan
from bot.improve import generate_cover_letter, review_cv
from bot.services.interview import handle_interview_practice, cancel_session, get_active_session

logger = logging.getLogger(__name__)

# Global constants
# Global constants
FREE_SEARCH_LIMIT = 10
FREE_ALERT_LIMIT = 1
PREMIUM_ALERT_LIMIT = 5

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
        
        # Account linking commands
        self.application.add_handler(CommandHandler("link", self.link_account_command))
        self.application.add_handler(CommandHandler("unlink", self.unlink_account_command))
        self.application.add_handler(CommandHandler("account", self.account_info_command))

        # Callback handlers
        self.application.add_handler(CallbackQueryHandler(self.handle_subscription_callback, pattern="^sub_currency_"))
        self.application.add_handler(CallbackQueryHandler(self.verify_payment, pattern=r"^verify_")) 
        self.application.add_handler(CallbackQueryHandler(self.show_job_details, pattern=r"^view_")) 
        self.application.add_handler(CallbackQueryHandler(self.save_job_callback, pattern=r"^save_"))
        self.application.add_handler(CallbackQueryHandler(self.back_to_results, pattern=r"^back_to_results$"))
        self.application.add_handler(CallbackQueryHandler(self.toggle_alert, pattern=r"^alert_"))

        # Helper for interview lock
    async def check_interview_lock(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Returns True if user is locked in an interview"""
        user = await self.get_user_or_create(update.effective_user)
        active_session = await get_active_session(user)
        
        if active_session:
            await update.message.reply_text(
                "⚠️ *Active Interview in Progress*\n\n"
                "You cannot use other commands right now.\n"
                "Type `exit` or `stop` to end the interview.",
                parse_mode=ParseMode.MARKDOWN
            )
            return True
        return False

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
        if await self.check_interview_lock(update, context): return
        user = await self.get_user_or_create(update.effective_user)

        if user.subscription_status != 'Paid':
            await self.send_upgrade_message(update, "CV Review")
            return

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
        if await self.check_interview_lock(update, context): return
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

        if user.subscription_status != 'Paid':
            await self.send_upgrade_message(update, "Cover Letter Generator")
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

        # Handle exit/stop
        if user_input.lower() in ['exit', 'stop', '/stop']:
            if await cancel_session(user):
                await update.message.reply_text("🛑 Interview cancelled. You can now use other commands.")
                return
            else:
                if user_input.lower() == '/stop': # Allow /stop to work even if no session
                     await update.message.reply_text("No active interview to stop.")
                     return

        # If it's the practice command, proceed. If it's another command, ignore.
        if user_input.startswith('/') and not user_input.lower().startswith("/practice"):
            return
            
        # If not starting and no active session, ignore (unless it's /practice)
        if not user_input.lower().startswith("/practice"):
             active_session = await get_active_session(user)
             if not active_session:
                 return

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
            "👋 *Welcome to Job Bot!* \n"
            "Your AI-powered career assistant.\n\n"
            "🔍 *Job Search*\n"
            "• `/findjobs <keywords>` - Search for jobs (e.g., `/findjobs python remote`)\n"
            "• `/history` - View your saved jobs\n\n"
            "📝 *CV & Application*\n"
            "• `/build_cv` - Create a professional CV\n"
            "• `/view_cv` - View your current CV\n"
            "• `/cv_review` - Get AI feedback on your CV\n"
            "• `/coverletter <Job> | <Company>` - Generate a cover letter\n\n"
            "🔔 *Alerts*\n"
            "• `/setalert <keyword>` - Create a job alert\n"
            "• `/myalerts` - Manage your alerts\n\n"
            "🚀 *Career Growth*\n"
            "• `/careerpath <role>` - Explore career progression\n"
            "• `/upskill <role>` - Get a personalized learning plan\n"
            "• `/practice` - Start a mock interview\n\n"
            "💎 *Premium*\n"
            "• `/subscribe` - Get unlimited searches & more alerts\n"
            "• `/quota` - Check your free search limit\n\n"
            f"ℹ️ _Free users get {FREE_SEARCH_LIMIT} searches per month and {FREE_ALERT_LIMIT} alert._",
            parse_mode=ParseMode.MARKDOWN
        )

    async def upskill_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if await self.check_interview_lock(update, context): return
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
        if await self.check_interview_lock(update, context): return
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
            await query.edit_message_text("❌ Job details no longer available.")
            return
        
        # Extract job information
        title = job.get('job_title', 'N/A')
        company = job.get('employer_name', 'Unknown')
        location = job.get('job_city', 'N/A')
        country = job.get('job_country', 'N/A')
        job_type = job.get('job_employment_type', 'N/A')
        posted = job.get('job_posted_at', 'N/A')
        is_remote = job.get('remote', False)
        
        # Build header with title and company
        message = f"💼 <b>{title}</b>\n\n"
        
        # Company and location section
        message += f"🏢 <b>Company:</b> {company}\n"
        
        # Location with remote badge
        if is_remote:
            message += f"📍 <b>Location:</b> {location}, {country} 🌐 <i>Remote</i>\n"
        else:
            message += f"📍 <b>Location:</b> {location}, {country}\n"
        
        # Employment type
        message += f"⏰ <b>Type:</b> {job_type}\n"
        
        # Posted date
        if posted and posted != 'N/A':
            # Try to format the date nicely
            try:
                from datetime import datetime
                if isinstance(posted, str):
                    # Handle ISO format or timestamp
                    if 'T' in posted:
                        dt = datetime.fromisoformat(posted.replace('Z', '+00:00'))
                        posted = dt.strftime('%B %d, %Y')
                message += f"📅 <b>Posted:</b> {posted}\n"
            except:
                message += f"📅 <b>Posted:</b> {posted}\n"
        
        # Salary information (if available)
        salary_min = job.get('job_min_salary')
        salary_max = job.get('job_max_salary')
        salary_currency = job.get('job_salary_currency', 'USD')
        
        if salary_min or salary_max:
            message += "\n💰 <b>Salary:</b> "
            if salary_min and salary_max:
                message += f"{salary_currency} {salary_min:,} - {salary_max:,}\n"
            elif salary_min:
                message += f"{salary_currency} {salary_min:,}+\n"
            elif salary_max:
                message += f"Up to {salary_currency} {salary_max:,}\n"
        
        # Required skills/qualifications (if available)
        required_skills = job.get('job_required_skills')
        if required_skills:
            message += f"\n✅ <b>Required Skills:</b>\n"
            if isinstance(required_skills, list):
                for skill in required_skills[:5]:  # Limit to 5 skills
                    message += f"  • {skill}\n"
            else:
                message += f"  {required_skills}\n"
        
        # Description section
        description = job.get('job_description', '')
        if description:
            message += f"\n📋 <b>Description:</b>\n"
            # Smart truncation - try to break at sentence or word boundary
            max_length = 800
            if len(description) > max_length:
                truncated = description[:max_length]
                # Try to break at last period or space
                last_period = truncated.rfind('.')
                last_space = truncated.rfind(' ')
                
                if last_period > max_length - 100:
                    description = truncated[:last_period + 1] + "..."
                elif last_space > max_length - 50:
                    description = truncated[:last_space] + "..."
                else:
                    description = truncated + "..."
            
            message += f"{description}\n"
        
        # Benefits (if available)
        benefits = job.get('job_benefits')
        if benefits:
            message += f"\n🎁 <b>Benefits:</b>\n"
            if isinstance(benefits, list):
                for benefit in benefits[:5]:
                    message += f"  • {benefit}\n"
            else:
                message += f"  {benefits}\n"
        
        # Application deadline (if available)
        deadline = job.get('job_offer_expiration_datetime_utc')
        if deadline:
            message += f"\n⏳ <b>Application Deadline:</b> {deadline}\n"
        
        # Build action buttons
        buttons = []
        
        # Apply button
        apply_url = job.get('job_apply_link')
        if apply_url:
            buttons.append([InlineKeyboardButton("🚀 Apply Now", url=apply_url)])
        
        # Save job button (always show - will handle if already saved)
        buttons.append([InlineKeyboardButton("💾 Save Job", callback_data=f"save_{job_id}")])
        
        # Back button
        buttons.append([InlineKeyboardButton("⬅️ Back to Results", callback_data="back_to_results")])
        
        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.HTML
        )

    async def save_job_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle save job button click"""
        query = update.callback_query
        
        job_id = query.data.split("_", 1)[1]
        user_id = str(update.effective_user.id)
        
        job = self.job_cache.get(job_id)
        if not job:
            await query.answer("❌ Job details no longer available.", show_alert=True)
            return
        
        title = job.get('job_title', 'N/A')
        company = job.get('employer_name', 'Unknown')
        
        try:
            # Check if already saved
            existing = await sync_to_async(Job.objects.filter)(user_id=user_id, job_id=job_id)
            if await sync_to_async(existing.exists)():
                await query.answer("✅ Job already saved!", show_alert=True)
            else:
                await self.save_job(user_id, job_id, title, company)
                await query.answer("💾 Job saved successfully!", show_alert=True)
        except Exception as e:
            logger.error(f"Error saving job: {e}")
            await query.answer("❌ Failed to save job. Please try again.", show_alert=True)

    async def find_jobs(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if await self.check_interview_lock(update, context): return
        user_id = str(update.effective_user.id)
        if not context.args:
            await update.message.reply_text(
                "🔍 *Job Search*\n\n"
                "Please provide keywords to search.\n"
                "Examples:\n"
                "• `/findjobs python remote`\n"
                "• `/findjobs marketing entry-level`\n"
                "• `/findjobs manager full-time`",
                parse_mode=ParseMode.MARKDOWN
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
                "❌ *No jobs found matching your criteria.*\n\n"
                "Try:\n"
                "• Using broader keywords\n"
                "• Removing some filters\n"
                "• Checking for typos",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        for job in jobs:
            job_id = job.get("job_id", str(hash(job.get('job_title', '') + job.get('employer_name', ''))))
            self.job_cache[job_id] = job
        
        message = f"🔍 Found *{len(jobs)}* jobs matching your search:\n\n"
        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
        
        # Determine how many jobs to show
        display_limit = len(jobs) if is_premium else 5
        jobs_to_show = jobs[:display_limit]

        for job in jobs_to_show:
            title = job.get('job_title', 'N/A')
            company = job.get('employer_name', 'Unknown')
            location = f"{job.get('job_city', 'N/A')}, {job.get('job_country', 'N/A')}"
            job_type = job.get('job_employment_type', 'N/A')
            job_id = job.get("job_id", str(hash(title + company)))
            is_remote = job.get('remote', False)
            posted = job.get('job_posted_at', 'N/A')
            
            # Format posted date
            posted_text = ""
            if posted and posted != 'N/A':
                try:
                    from datetime import datetime
                    if isinstance(posted, str) and 'T' in posted:
                        dt = datetime.fromisoformat(posted.replace('Z', '+00:00'))
                        # Show relative time if recent
                        days_ago = (datetime.now(dt.tzinfo) - dt).days
                        if days_ago == 0:
                            posted_text = "📅 Today"
                        elif days_ago == 1:
                            posted_text = "📅 Yesterday"
                        elif days_ago < 7:
                            posted_text = f"📅 {days_ago} days ago"
                        else:
                            posted_text = f"📅 {dt.strftime('%b %d')}"
                    else:
                        posted_text = f"📅 {posted}"
                except:
                    posted_text = f"📅 {posted}"
            
            await self.save_job(user_id, job_id, title, company)
            
            # Build job card message
            job_message = f"💼 <b>{title}</b>\n"
            job_message += f"🏢 {company}\n"
            
            # Location with remote badge
            if is_remote:
                job_message += f"📍 {location} 🌐 <i>Remote</i>\n"
            else:
                job_message += f"📍 {location}\n"
            
            job_message += f"⏰ {job_type}"
            
            if posted_text:
                job_message += f" • {posted_text}"
            
            keyboard = [[InlineKeyboardButton("👁️ View Details", callback_data=f"view_{job_id}")]]
            await update.message.reply_text(
                job_message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.HTML
            )
        
        if not is_premium and len(jobs) > 5:
            await update.message.reply_text(
                f"⚠️ Showing top 5 results. *Upgrade to Premium* to see all {len(jobs)} jobs!",
                parse_mode=ParseMode.MARKDOWN
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
        
        user = await self.get_user(user_id)
        if not user:
            await update.message.reply_text("Please register first with /start")
            return
            
        # Store email in user_data for the callback
        context.user_data['subscribe_email'] = email
        
        buttons = [
            [InlineKeyboardButton("🇳🇬 Pay with NGN (Paystack)", callback_data="sub_currency_NGN")],
            [InlineKeyboardButton("🇺🇸 Pay with USD (Flutterwave)", callback_data="sub_currency_USD")]
        ]
        
        await update.message.reply_text(
            "� *Choose your currency*\n\n"
            "Select your preferred currency for the Premium subscription:",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.MARKDOWN
        )

    async def handle_subscription_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        currency = query.data.split("_")[2]  # sub_currency_NGN or sub_currency_USD
        user_id = str(update.effective_user.id)
        email = context.user_data.get('subscribe_email')
        
        if not email:
            await query.edit_message_text("Session expired. Please start over with /subscribe <email>")
            return
            
        provider = 'paystack' if currency == 'NGN' else 'flutterwave'
        reference = f"{provider.upper()}_{user_id}_{int(time.time())}"
        
        try:
            if provider == 'paystack':
                data = create_paystack_payment(email, 4500, reference)
                if not data.get("status"):
                    raise Exception("Failed to create Paystack payment")
                url = data['data']['authorization_url']
                amount_display = "NGN 4,500"
                
            else:  # flutterwave
                data = create_flutterwave_payment(email, 9.99, 'USD', reference)
                if data.get("status") == "error":
                    raise Exception("Failed to create Flutterwave payment")
                url = data['data']['link']
                amount_display = "$9.99"
            
            # Update user status
            await self.update_user_status(user_id, "Pending", reference)
            
            # Update User model with provider
            user = await self.get_user(user_id)
            if user:
                user.payment_provider = provider
                await sync_to_async(user.save)()
            
            buttons = [
                [InlineKeyboardButton(f"Pay {amount_display}", url=url)],
                [InlineKeyboardButton("Verify Payment", callback_data=f"verify_{reference}")]
            ]
            
            await query.edit_message_text(
                f"💳 *Complete your payment*\n\n"
                f"Amount: *{amount_display}*\n"
                f"Provider: *{provider.title()}*\n\n"
                f"Click the link below to pay securely.",
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Payment creation error: {e}")
            await query.edit_message_text("❌ Error creating payment link. Please try again later.")

    async def verify_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        ref = query.data.split("_", 1)[1]
        user_id = str(update.effective_user.id)
        
        # Auto-detect provider
        if ref.startswith('PAYSTACK_'):
            provider = 'paystack'
        elif ref.startswith('FLUTTERWAVE_') or ref.startswith('FLW_'):
            provider = 'flutterwave'
        else:
            provider = 'paystack'  # Default/Legacy
        
        try:
            success = False
            if provider == 'paystack':
                result = verify_paystack_payment(ref)
                success = result.get("data", {}).get("status") == "success"
            else:
                result = verify_flutterwave_payment(ref)
                success = result.get("data", {}).get("status") == "successful"
                
            if success:
                await self.update_user_status(user_id, "Paid", ref)
                await query.edit_message_text("✅ *Payment Verified!* You are now a Premium user. Enjoy unlimited searches!", parse_mode=ParseMode.MARKDOWN)
            else:
                await query.edit_message_text("Verification failed or still pending. Please try again later.")
        except Exception as e:
            logger.error(f"Payment verification error: {e}")
            await query.edit_message_text("An error occurred during verification.")

    async def set_alert(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Fixed version that guarantees alert saving"""
        user_id = str(update.effective_user.id)
        logger.info(f"SET ALERT STARTED for {user_id}")

        # Input validation
        if not context.args:
            await update.message.reply_text("❗ Usage: `/setalert <keyword>`", parse_mode=ParseMode.MARKDOWN)
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

            limit = PREMIUM_ALERT_LIMIT if user.subscription_status == 'Paid' else FREE_ALERT_LIMIT
            
            if active_count >= limit:
                msg = f"❌ You've reached your limit of {limit} alert(s)."
                if user.subscription_status != 'Paid':
                    msg += "\nUse /subscribe to get up to 5 alerts!"
                await update.message.reply_text(msg)
                return

            # 4. Create and verify alert
            alert = await self.create_alert(user_id, query)
            if not alert:
                raise ValueError("Alert creation returned None")

            # SUCCESS - send confirmation
            await update.message.reply_text(
                f"✅ *Alert Saved!*\n\n"
                f"🆔 ID: `{alert.id}`\n"
                f"🔍 Query: `{query}`\n\n"
                "You'll be notified when new jobs match this query.",
                parse_mode=ParseMode.MARKDOWN
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
        await update.message.reply_text(f"📊 You have *{remaining}* free searches remaining today.", parse_mode=ParseMode.MARKDOWN)

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
                await update.message.reply_text("✅ Payment verified successfully! You are now a *Premium* user.", parse_mode=ParseMode.MARKDOWN)
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
                "🔕 You don't have any job alerts set up.\n\n"
                "Use `/setalert <keyword>` to create your first alert!",
                parse_mode=ParseMode.MARKDOWN
            )
            return
    
        message = "Your Job Alerts:\n\n"
        for alert in alerts:
            status = "✅ Active" if alert.active else "❌ Inactive"
            message += (
                f"🆔 ID: `{alert.id}`\n"
                f"🔍 Query: `{alert.query}`\n"
                f"Status: {status}\n"
                f"📅 Created: {alert.created_at.strftime('%Y-%m-%d')}\n\n"
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
            f"Alert for '{alert.query}' has been *{status}*.\n\n"
            "Use /myalerts to manage your alerts.",
            parse_mode=ParseMode.MARKDOWN
        )

    async def send_upgrade_message(self, update: Update, feature_name: str):
        await update.message.reply_text(
            f"💎 *Premium Feature Locked*\n\n"
            f"The *{feature_name}* is available only to Premium users.\n\n"
            "Upgrade now to access:\n"
            "✅ Unlimited Job Searches\n"
            "✅ 5 Active Job Alerts\n"
            "✅ CV Review & Cover Letter Generator\n\n"
            "Use `/subscribe <email>` to upgrade!",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def link_account_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Generate a code to link Telegram account to web profile"""
        if await self.check_interview_lock(update, context): return
        
        user_id = str(update.effective_user.id)
        username = update.effective_user.username
        
        # First try to find existing user by user_id or telegram_id
        platform_user = await sync_to_async(
            User.objects.select_related('tenant_user__tenant').filter(user_id=user_id).first
        )()
        
        if not platform_user:
            # Try by telegram_id
            platform_user = await sync_to_async(
                User.objects.select_related('tenant_user__tenant').filter(telegram_id=user_id).first
            )()
        
        if not platform_user:
            # Create new user
            platform_user = await sync_to_async(User.objects.create)(
                user_id=user_id,
                telegram_id=user_id,
                username=username,
                platform_type='telegram'
            )
        else:
            # Update telegram_id if not set
            if not platform_user.telegram_id:
                platform_user.telegram_id = user_id
                platform_user.username = username
                await sync_to_async(platform_user.save)()
        
        # Check if already linked
        if platform_user.tenant_user:
            await update.message.reply_text(
                f"✅ *Account Already Linked*\\n\\n"
                f"Your Telegram account is linked to:\\n"
                f"📧 {platform_user.tenant_user.email}\\n"
                f"🏢 {platform_user.tenant_user.tenant.name}\\n\\n"
                f"Use /unlink to disconnect.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Generate link code
        code = await sync_to_async(platform_user.generate_link_code)()
        
        await update.message.reply_text(
            f"🔗 *Link Your Account*\\n\\n"
            f"Your linking code: `{code}`\\n\\n"
            f"⏰ This code expires in 15 minutes.\\n\\n"
            f"*To link your account:*\\n"
            f"1. Go to https://job.pluggedspace.org/settings/link\\n"
            f"2. Enter this code\\n"
            f"3. Your Telegram and web accounts will be linked!\\n\\n"
            f"*Benefits:*\\n"
            f"✅ Unified job alerts across platforms\\n"
            f"✅ Shared subscription status\\n"
            f"✅ Access your data from web or Telegram\\n"
            f"✅ Sync your CV and saved jobs",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def unlink_account_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Unlink Telegram account from web profile"""
        if await self.check_interview_lock(update, context): return
        
        user_id = str(update.effective_user.id)
        
        try:
            platform_user = await sync_to_async(User.objects.select_related('tenant_user').get)(telegram_id=user_id)
        except User.DoesNotExist:
            await update.message.reply_text(
                "❌ No Telegram account found. Use /start to register first."
            )
            return
        
        if not platform_user.tenant_user:
            await update.message.reply_text(
                "ℹ️ Your Telegram account is not linked to any web profile.\\n\\n"
                "Use /link to link your account.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Store email for confirmation message
        email = platform_user.tenant_user.email
        
        # Unlink
        platform_user.tenant_user = None
        await sync_to_async(platform_user.save)()
        
        await update.message.reply_text(
            f"✅ *Account Unlinked*\\n\\n"
            f"Your Telegram account has been disconnected from:\\n"
            f"📧 {email}\\n\\n"
            f"You can link to a different account anytime using /link",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def account_info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show account information and linking status"""
        if await self.check_interview_lock(update, context): return
        
        user_id = str(update.effective_user.id)
        
        try:
            platform_user = await sync_to_async(User.objects.select_related('tenant_user__tenant').get)(telegram_id=user_id)
        except User.DoesNotExist:
            await update.message.reply_text(
                "❌ No account found. Use /start to register first."
            )
            return
        
        # Build account info message
        message = f"👤 *Your Account Info*\\n\\n"
        message += f"*Telegram:*\\n"
        message += f"• Username: @{platform_user.username or 'Not set'}\\n"
        message += f"• User ID: `{platform_user.telegram_id}`\\n"
        message += f"• Subscription: {platform_user.subscription_status}\\n"
        message += f"• Searches: {platform_user.search_count}/{FREE_SEARCH_LIMIT}\\n\\n"
        
        if platform_user.tenant_user:
            message += f"*🔗 Linked Web Account:*\\n"
            message += f"• Email: {platform_user.tenant_user.email}\\n"
            message += f"• Name: {platform_user.tenant_user.full_name or 'Not set'}\\n"
            message += f"• Organization: {platform_user.tenant_user.tenant.name}\\n"
            message += f"• Role: {platform_user.tenant_user.role.title()}\\n\\n"
            message += f"Use /unlink to disconnect"
        else:
            message += f"*🔗 Account Linking:*\\n"
            message += f"Not linked to any web account\\n\\n"
            message += f"Use /link to link your account"
        
        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

    def run(self):
        self.application.run_polling()

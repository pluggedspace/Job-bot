"""
WhatsApp Bot Implementation for Job Bot
Using Meta (Facebook) WhatsApp Business API

Setup:
1. Install: pip install requests
2. Configure .env:
   - META_ACCESS_TOKEN=your_permanent_token
   - META_PHONE_NUMBER_ID=your_phone_number_id
   - META_VERIFY_TOKEN=your_custom_verify_token (for webhook verification)
3. Set webhook in Meta Developer Console: /api/whatsapp/webhook
"""

import logging
import requests
import asyncio
from django.conf import settings
from django.db import transaction
from asgiref.sync import sync_to_async

from bot.models import User, Job, Alert
from bot.utils import create_paystack_payment, verify_paystack_payment
from bot.functions.jobs import get_all_jobs
from bot.services.career_path import resolve_career_path
from bot.services.upskill import get_upskill_plan
from bot.improve import generate_cover_letter, review_cv
from bot.services.interview import handle_interview_practice, cancel_session, get_active_session

logger = logging.getLogger(__name__)

# Constants
FREE_SEARCH_LIMIT = 10
FREE_ALERT_LIMIT = 1
PREMIUM_ALERT_LIMIT = 5

# Meta WhatsApp API Configuration
META_API_URL = "https://graph.facebook.com/v18.0"


class WhatsAppBot:
    def __init__(self):
        self.access_token = settings.META_ACCESS_TOKEN
        self.phone_number_id = settings.META_PHONE_NUMBER_ID
        self.verify_token = settings.META_VERIFY_TOKEN
    
    def send_message(self, to_number: str, message: str):
        """Send a WhatsApp message using Meta API"""
        url = f"{META_API_URL}/{self.phone_number_id}/messages"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_number,
            "type": "text",
            "text": {
                "preview_url": True,
                "body": message
            }
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            logger.info(f"WhatsApp message sent to {to_number}")
            return response.json()
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message: {e}", exc_info=True)
            return None
    
    def mark_as_read(self, message_id: str):
        """Mark message as read"""
        url = f"{META_API_URL}/{self.phone_number_id}/messages"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }
        
        try:
            requests.post(url, json=payload, headers=headers)
        except Exception as e:
            logger.error(f"Failed to mark message as read: {e}")
    
    async def handle_message(self, from_number: str, message_body: str, message_id: str = None):
        """Main message handler - routes to appropriate command"""
        # Get or create user
        user = await self.get_or_create_user(from_number)
        
        # Mark message as read
        if message_id:
            self.mark_as_read(message_id)
        
        # Check for active interview session
        active_session = await get_active_session(user)
        
        # Handle exit from interview
        if active_session and message_body.lower() in ['exit', 'stop']:
            if await cancel_session(user):
                self.send_message(from_number, "🛑 Interview cancelled. You can now use other commands.")
            return
        
        # If in interview, handle as interview response
        if active_session:
            result = await handle_interview_practice(user, message_body)
            self.send_message(from_number, result)
            return
        
        # Parse command
        message_lower = message_body.lower().strip()
        
        # Route to command handlers
        if message_lower.startswith('/start') or message_lower == 'start':
            await self.start_command(from_number, user)
        elif message_lower.startswith('/findjobs'):
            await self.find_jobs(from_number, user, message_body)
        elif message_lower.startswith('/subscribe'):
            await self.subscribe(from_number, user, message_body)
        elif message_lower.startswith('/setalert'):
            await self.set_alert(from_number, user, message_body)
        elif message_lower.startswith('/myalerts'):
            await self.my_alerts(from_number, user)
        elif message_lower.startswith('/quota'):
            await self.check_quota(from_number, user)
        elif message_lower.startswith('/history'):
            await self.history(from_number, user)
        elif message_lower.startswith('/careerpath'):
            await self.careerpath_command(from_number, user, message_body)
        elif message_lower.startswith('/upskill'):
            await self.upskill_command(from_number, user, message_body)
        elif message_lower.startswith('/coverletter'):
            await self.coverletter_handler(from_number, user, message_body)
        elif message_lower.startswith('/cv_review'):
            await self.cv_review_handler(from_number, user)
        elif message_lower.startswith('/practice'):
            await self.interview_practice_handler(from_number, user)
        elif message_lower.startswith('/link'):
            await self.link_account_command(from_number, user)
        elif message_lower.startswith('/unlink'):
            await self.unlink_account_command(from_number, user)
        elif message_lower.startswith('/account'):
            await self.account_info_command(from_number, user)
        else:
            self.send_message(from_number, 
                "Unknown command. Send /start to see available commands.")
    
    @sync_to_async
    def get_or_create_user(self, phone: str):
        """Get or create WhatsApp user"""
        user, created = User.objects.get_or_create(
            whatsapp_id=phone,
            defaults={
                'user_id': phone,
                'username': phone,
                'platform_type': 'whatsapp'
            }
        )
        return user
    
    async def start_command(self, phone: str, user):
        """Send welcome message"""
        message = (
            "👋 *Welcome to Job Bot!*\n"
            "Your AI-powered career assistant.\n\n"
            "🔍 *Job Search*\n"
            "• /findjobs <keywords> - Search for jobs\n"
            "• /history - View your saved jobs\n\n"
            "📝 *CV & Application*\n"
            "• /cv_review - Get AI feedback on your CV\n"
            "• /coverletter <Job> | <Company> - Generate a cover letter\n\n"
            "🔔 *Alerts*\n"
            "• /setalert <keyword> - Create a job alert\n"
            "• /myalerts - Manage your alerts\n\n"
            "🚀 *Career Growth*\n"
            "• /careerpath <role> - Explore career progression\n"
            "• /upskill <role> - Get a personalized learning plan\n"
            "• /practice - Start a mock interview\n\n"
            "💎 *Premium*\n"
            "• /subscribe - Get unlimited searches & more alerts\n"
            "• /quota - Check your free search limit\n\n"
            f"ℹ️ _Free users get {FREE_SEARCH_LIMIT} searches per month and {FREE_ALERT_LIMIT} alert._"
        )
        self.send_message(phone, message)
    
    async def find_jobs(self, phone: str, user, message: str):
        """Search for jobs"""
        query = message.replace('/findjobs', '').strip()
        if not query:
            self.send_message(phone,
                "🔍 *Job Search*\n\n"
                "Please provide keywords to search.\n"
                "Example: /findjobs python remote")
            return
        
        is_premium = user.subscription_status == 'Paid'
        if not is_premium and user.search_count >= FREE_SEARCH_LIMIT:
            self.send_message(phone,
                f"You've reached your monthly limit of {FREE_SEARCH_LIMIT} free searches.\n"
                "Use /subscribe to upgrade to premium for unlimited searches!")
            return
        
        if not is_premium:
            user.search_count += 1
            await sync_to_async(user.save)()
        
        self.send_message(phone, "🔍 Searching for jobs...")
        
        filters = {}
        if "remote" in query.lower():
            filters["remote"] = True
        
        jobs = get_all_jobs(query, filters)
        
        if not jobs:
            self.send_message(phone, "❌ No jobs found matching your criteria. Try broader keywords.")
            return
        
        display_limit = min(len(jobs), 5 if not is_premium else 10)
        
        message = f"Found *{len(jobs)}* jobs matching '{query}':\n\n"
        self.send_message(phone, message)
        
        for job in jobs[:display_limit]:
            title = job.get('job_title', 'N/A')
            company = job.get('employer_name', 'Unknown')
            location = f"{job.get('job_city', 'N/A')}, {job.get('job_country', 'N/A')}"
            remote = "🌐 Remote" if job.get('remote') else ""
            apply_link = job.get('job_apply_link', '')
            
            job_msg = (
                f"💼 *{title}*\n"
                f"🏢 {company}\n"
                f"📍 {location} {remote}\n"
            )
            if apply_link:
                job_msg += f"🔗 Apply: {apply_link}\n"
            
            self.send_message(phone, job_msg)
        
        if not is_premium and len(jobs) > 5:
            self.send_message(phone,
                f"⚠️ Showing top 5 results. *Upgrade to Premium* to see all {len(jobs)} jobs!\n"
                "Use /subscribe to upgrade.")
    
    async def subscribe(self, phone: str, user, message: str):
        """Handle subscription"""
        parts = message.split()
        if len(parts) < 2:
            self.send_message(phone,
                "Please provide your email.\n"
                "Usage: /subscribe your_email@example.com")
            return
        
        email = parts[1]
        reference = f"REF_{user.user_id}_{int(asyncio.get_event_loop().time())}"
        
        data = create_paystack_payment(email, 750, reference)
        
        if not data.get("status"):
            self.send_message(phone, "Error creating payment link. Please try again.")
            return
        
        user.subscription_status = "Pending"
        user.payment_reference = reference
        await sync_to_async(user.save)()
        
        url = data['data']['authorization_url']
        message_text = (
            "💳 *Complete your payment*\n\n"
            f"Amount: ZAR 750\n"
            f"Reference: {reference}\n\n"
            f"Pay here: {url}\n\n"
            f"After payment, send: /verify {reference}"
        )
        self.send_message(phone, message_text)
    
    async def set_alert(self, phone: str, user, message: str):
        """Create job alert"""
        query = message.replace('/setalert', '').strip()
        
        if not query or len(query) < 2:
            self.send_message(phone, "Please provide a search keyword. Usage: /setalert python developer")
            return
        
        limit = PREMIUM_ALERT_LIMIT if user.subscription_status == 'Paid' else FREE_ALERT_LIMIT
        active_count = await sync_to_async(
            Alert.objects.filter(user=user, active=True).count
        )()
        
        if active_count >= limit:
            msg = f"❌ You've reached your limit of {limit} alert(s)."
            if user.subscription_status != 'Paid':
                msg += "\nUse /subscribe to get up to 5 alerts!"
            self.send_message(phone, msg)
            return
        
        try:
            with transaction.atomic():
                alert = await sync_to_async(Alert.objects.create)(
                    user=user,
                    query=query,
                    active=True
                )
                self.send_message(phone,
                    f"✅ *Alert Saved!*\n\n"
                    f"Query: {query}\n\n"
                    "You'll be notified when new jobs match this query.")
        except Exception as e:
            logger.error(f"Alert creation failed: {e}", exc_info=True)
            self.send_message(phone, "⚠️ Failed to save alert. Please try again.")
    
    async def my_alerts(self, phone: str, user):
        """List user alerts"""
        alerts = await sync_to_async(list)(
            Alert.objects.filter(user=user).order_by('-created_at')
        )
        
        if not alerts:
            self.send_message(phone,
                "🔕 You don't have any job alerts set up.\n\n"
                "Use /setalert <keyword> to create your first alert!")
            return
        
        message = "Your Job Alerts:\n\n"
        for alert in alerts:
            status = "✅ Active" if alert.active else "❌ Inactive"
            message += (
                f"🔍 {alert.query}\n"
                f"Status: {status}\n"
                f"Created: {alert.created_at.strftime('%Y-%m-%d')}\n\n"
            )
        
        self.send_message(phone, message)
    
    async def check_quota(self, phone: str, user):
        """Check search quota"""
        if user.subscription_status == 'Paid':
            self.send_message(phone, "You have unlimited access as a premium user.")
            return
        
        remaining = max(0, FREE_SEARCH_LIMIT - user.search_count)
        self.send_message(phone, f"📊 You have *{remaining}* free searches remaining.")
    
    async def history(self, phone: str, user):
        """Show saved jobs"""
        jobs = await sync_to_async(list)(
            Job.objects.filter(user=user).order_by('-saved_at')[:10]
        )
        
        if not jobs:
            self.send_message(phone, "You haven't saved any jobs yet.")
            return
        
        message = "*Your recent saved jobs:*\n\n"
        for idx, job in enumerate(jobs, 1):
            message += f"{idx}. {job.title} at {job.company}\n"
        
        self.send_message(phone, message)
    
    async def careerpath_command(self, phone: str, user, message: str):
        """Career path exploration"""
        role = message.replace('/careerpath', '').strip()
        
        if not role:
            self.send_message(phone, "Please specify a job title. Example: /careerpath software engineer")
            return
        
        data, source = await sync_to_async(resolve_career_path)(role)
        
        if "error" in data:
            self.send_message(phone, f"❌ {data['error']}")
            return
        
        msg = f"📈 *Career Path for {data['input_title']}* (via {source})\n\n"
        msg += f"*Broader Roles:* {', '.join(data.get('broader', []) or ['N/A'])}\n"
        msg += f"*Narrower Roles:* {', '.join(data.get('narrower', []) or ['N/A'])}\n"
        msg += f"*Related:* {', '.join(data.get('related', []) or ['N/A'])}"
        
        self.send_message(phone, msg)
    
    async def upskill_command(self, phone: str, user, message: str):
        """Upskill plan generator"""
        target_role = message.replace('/upskill', '').strip()
        
        if not target_role:
            self.send_message(phone, "Please specify a target role. Example: /upskill data scientist")
            return
        
        plan = await sync_to_async(get_upskill_plan)(user, target_role)
        
        if not plan or not plan.get('target'):
            self.send_message(phone, "⚠️ Could not generate an upskill plan. Please try a different role.")
            return
        
        msg = f"📚 *Upskill Plan for {plan['target']}*\n\n"
        
        if plan.get('skills_to_gain'):
            msg += "*Skills to gain:*\n"
            for skill in plan['skills_to_gain']:
                skill_name = skill.get('name')
                course = skill.get('course', {})
                course_title = course.get('title', 'Free course')
                course_url = course.get('url', '#')
                msg += f"• *{skill_name}*\n  {course_title}: {course_url}\n"
        
        if plan.get('note'):
            msg += f"\nℹ️ _{plan['note']}_"
        
        self.send_message(phone, msg)
    
    async def coverletter_handler(self, phone: str, user, message: str):
        """Generate cover letter (Premium)"""
        if user.subscription_status != 'Paid':
            self.send_message(phone,
                "💎 *Premium Feature*\n\n"
                "Cover Letter Generator is available only to Premium users.\n"
                "Use /subscribe to upgrade!")
            return
        
        try:
            parts = message.replace("/coverletter", "").strip().split("|")
            job_title = parts[0].strip()
            company = parts[1].strip() if len(parts) > 1 else None
        except Exception:
            self.send_message(phone, "Usage: /coverletter Job Title | Company Name")
            return
        
        self.send_message(phone, "🧠 Generating your cover letter...")
        
        result = await sync_to_async(generate_cover_letter)(user, job_title, company)
        
        if result.get("error"):
            self.send_message(phone,
                f"⚠️ Missing profile fields: {', '.join(result['missing_fields'])}\n"
                "Please complete your profile first.")
        else:
            self.send_message(phone,
                f"📄 *Cover Letter for {job_title} at {company or 'Company'}*\n\n"
                f"{result['cover_letter']}")
    
    async def cv_review_handler(self, phone: str, user):
        """CV review (Premium)"""
        if user.subscription_status != 'Paid':
            self.send_message(phone,
                "💎 *Premium Feature*\n\n"
                "CV Review is available only to Premium users.\n"
                "Use /subscribe to upgrade!")
            return
        
        self.send_message(phone, "🔍 Reviewing your CV...")
        
        result = await sync_to_async(review_cv)(user)
        
        if result.get("error"):
            self.send_message(phone,
                f"⚠️ Missing profile fields: {', '.join(result['missing_fields'])}\n"
                "Please complete your profile first.")
        else:
            self.send_message(phone, f"📋 *CV Review Report:*\n\n{result['cv_review']}")
    
    async def interview_practice_handler(self, phone: str, user):
        """Start interview practice (Premium)"""
        if user.subscription_status != 'Paid':
            self.send_message(phone,
                "💎 *Premium Feature*\n\n"
                "Interview Practice is available only to Premium users.\n"
                "Use /subscribe to upgrade!")
            return
        
        self.send_message(phone, "🎤 Starting your mock interview... Get ready!")
        
        result = await handle_interview_practice(user, None)
        self.send_message(phone, result)
    
    async def link_account_command(self, phone: str, user):
        """Generate account linking code"""
        if user.tenant_user:
            self.send_message(phone,
                f"✅ *Account Already Linked*\n\n"
                f"Your WhatsApp account is linked to:\n"
                f"📧 {user.tenant_user.email}\n"
                f"🏢 {user.tenant_user.tenant.name}\n\n"
                "Use /unlink to disconnect.")
            return
        
        code = await sync_to_async(user.generate_link_code)()
        
        self.send_message(phone,
            f"🔗 *Link Your Account*\n\n"
            f"Your linking code: `{code}`\n\n"
            f"⏰ This code expires in 15 minutes.\n\n"
            f"*To link your account:*\n"
            f"1. Go to https://job.pluggedspace.org/settings/link\n"
            f"2. Enter this code\n"
            f"3. Your WhatsApp and web accounts will be linked!")
    
    async def unlink_account_command(self, phone: str, user):
        """Unlink account"""
        if not user.tenant_user:
            self.send_message(phone,
                "ℹ️ Your WhatsApp account is not linked to any web profile.\n"
                "Use /link to link your account.")
            return
        
        email = user.tenant_user.email
        user.tenant_user = None
        await sync_to_async(user.save)()
        
        self.send_message(phone,
            f"✅ *Account Unlinked*\n\n"
            f"Your WhatsApp account has been disconnected from:\n"
            f"📧 {email}\n\n"
            "You can link to a different account anytime using /link")
    
    async def account_info_command(self, phone: str, user):
        """Show account information"""
        message = f"👤 *Your Account Info*\n\n"
        message += f"*WhatsApp:* {user.whatsapp_id}\n"
        message += f"*Subscription:* {user.subscription_status}\n"
        message += f"*Searches:* {user.search_count}/{FREE_SEARCH_LIMIT}\n\n"
        
        if user.tenant_user:
            message += f"*🔗 Linked Web Account:*\n"
            message += f"• Email: {user.tenant_user.email}\n"
            message += f"• Name: {user.tenant_user.full_name or 'Not set'}\n"
            message += f"• Organization: {user.tenant_user.tenant.name}\n\n"
            message += "Use /unlink to disconnect"
        else:
            message += f"*🔗 Account Linking:*\n"
            message += "Not linked to any web account\n\n"
            message += "Use /link to link your account"
        
        self.send_message(phone, message)


# Global bot instance
whatsapp_bot = WhatsAppBot()

from celery import shared_task
from django.conf import settings
from bot.functions.jobs import get_jobs
from bot.models import Alert
from telegram import Bot
from telegram.constants import ParseMode
import logging

logger = logging.getLogger(__name__)

@shared_task(name='bot.tasks.check_alerts')
def check_alerts():
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    alerts = Alert.objects.filter(active=True)
    
    for alert in alerts:
        try:
            # Get jobs posted in the last 24 hours
            jobs = get_jobs(
                alert.query,
                filters={
                    "date_posted": "day",
                    "sort_by": "date"
                }
            )
            
            if jobs:
                # Format the alert message
                message = f"🔔 New jobs found for '{alert.query}':\n\n"
                
                for job in jobs[:5]:  # Send top 5 most relevant jobs
                    title = job.get('job_title', 'N/A')
                    company = job.get('employer_name', 'Unknown')
                    location = f"{job.get('job_city', 'N/A')}, {job.get('job_country', 'N/A')}"
                    job_type = job.get('job_employment_type', 'N/A')
                    posted_at = job.get('job_posted_at', 'N/A')
                    apply_url = job.get('job_apply_link', '')
                    
                    message += (
                        f"<b>{title}</b>\n"
                        f"🏢 Company: {company}\n"
                        f"📍 Location: {location}\n"
                        f"💼 Type: {job_type}\n"
                        f"⏰ Posted: {posted_at}\n"
                    )
                    
                    if apply_url:
                        message += f"🔗 <a href='{apply_url}'>Apply Now</a>\n"
                    
                    message += "\n"
                
                if len(jobs) > 5:
                    message += f"... and {len(jobs) - 5} more jobs found.\n"
                
                message += "\nUse /findjobs to search for more jobs or /myalerts to manage your alerts."
                
                # Send the alert
                bot.send_message(
                    chat_id=alert.user.user_id,
                    text=message,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )
                
        except Exception as e:
            logger.error(f"Error checking alert {alert.id}: {e}")

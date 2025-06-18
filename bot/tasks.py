from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution
from django.conf import settings
from bot.utils import get_jobs
from bot.models import Alert, User
from telegram import Bot, ParseMode
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

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

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")
    
    # Check alerts every 30 minutes
    scheduler.add_job(
        check_alerts,
        trigger="interval",
        minutes=30,
        id="check_alerts",
        max_instances=1,
        replace_existing=True,
    )
    
    try:
        scheduler.start()
    except KeyboardInterrupt:
        scheduler.shutdown()
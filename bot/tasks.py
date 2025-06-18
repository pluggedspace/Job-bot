from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution
from django.conf import settings
from bot.utils import get_jobs
from bot.models import Alert, User
from telegram import Bot
import logging

logger = logging.getLogger(__name__)

def check_alerts():
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    alerts = Alert.objects.filter(active=True)
    
    for alert in alerts:
        try:
            jobs = get_jobs(alert.query)
            if jobs:
                msg = f"New jobs for {alert.query}:\n"
                for job in jobs[:3]:
                    msg += f"{job.get('job_title')} at {job.get('employer_name')}\n"
                bot.send_message(chat_id=alert.user.user_id, text=msg)
        except Exception as e:
            logger.error(f"Error checking alert {alert.id}: {e}")

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")
    
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
import sys
from django.apps import AppConfig
from django.conf import settings

class BotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bot'

    def ready(self):
        # Only start scheduler if the command is to run the server, NOT during migrations or other commands
        if 'runserver' in sys.argv or 'gunicorn' in sys.argv:
            from bot.tasks import start_scheduler
            start_scheduler()

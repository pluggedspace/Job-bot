# bot/management/commands/run_bot.py
from django.core.management.base import BaseCommand
from bot.bot import JobSearchBot

class Command(BaseCommand):
    help = 'Run the Telegram bot'

    def handle(self, *args, **kwargs):
        bot = JobSearchBot()
        bot.run()

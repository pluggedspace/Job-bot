from django.core.management.base import BaseCommand
from django.conf import settings
from telegram import Bot

class Command(BaseCommand):
    help = 'Set Telegram webhook'

    def handle(self, *args, **options):
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        webhook_url = "https://jobbot.pluggedspace.org/webhook"
        bot.set_webhook(webhook_url)
        self.stdout.write(self.style.SUCCESS(f'Webhook set to {webhook_url}'))
import os

from django.core.management.base import BaseCommand
from telegram import Bot
from django.conf import settings


class Command(BaseCommand):
    help = "Set Telegram webhook URL"

    def handle(self, *args, **kwargs):
        webhook_url = os.getenv("TELEGRAM_WEBHOOK_URL")
        if not webhook_url:
            self.stderr.write("Set TELEGRAM_WEBHOOK_URL in your environment, e.g. https://your-domain/webhook/")
            return

        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        bot.set_webhook(webhook_url)
        self.stdout.write(self.style.SUCCESS(f"Webhook set to {webhook_url}"))

# bot/management/commands/set_telegram_webhook.py
from django.core.management.base import BaseCommand
from telegram import Bot
from django.conf import settings

class Command(BaseCommand):
    help = 'Set Telegram webhook'

    def handle(self, *args, **kwargs):
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        url = "https://jobbot.pluggedspace.org/webhook"
        bot.set_webhook(url)
        self.stdout.write(self.style.SUCCESS(f"Webhook set to {url}"))

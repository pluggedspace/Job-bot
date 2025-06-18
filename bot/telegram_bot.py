# telegram_bot.py
from telegram.ext import ApplicationBuilder, CommandHandler
import os

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

bot_app = ApplicationBuilder().token(TOKEN).build()

# Add a simple handler
async def start(update, context):
    await update.message.reply_text("Hello! I'm alive.")

bot_app.add_handler(CommandHandler("start", start))


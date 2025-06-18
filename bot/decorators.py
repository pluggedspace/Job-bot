from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from bot.models import User

def subscription_required(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = str(update.effective_user.id)
        try:
            user = User.objects.get(user_id=user_id)
            if user.subscription_status != 'Paid':
                msg = "You need to subscribe to use this feature. Use /subscribe to proceed."
                if update.callback_query:
                    await update.callback_query.answer("Subscription required")
                    await update.callback_query.message.reply_text(msg)
                else:
                    await update.message.reply_text(msg)
                return
            return await func(update, context, *args, **kwargs)
        except User.DoesNotExist:
            msg = "Please register first with /start"
            await update.message.reply_text(msg)
    return wrapper
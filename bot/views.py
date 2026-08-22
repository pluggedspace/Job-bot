from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
import json
import logging
from telegram import Update

logger = logging.getLogger(__name__)

_bot_instance = None


def get_telegram_application():
    global _bot_instance
    if _bot_instance is None:
        from bot.bot import JobSearchBot

        _bot_instance = JobSearchBot()
    return _bot_instance.application


@csrf_exempt
def telegram_webhook(request):
    if request.method == "POST":
        try:
            application = get_telegram_application()
            update_data = json.loads(request.body.decode("utf-8"))
            update = Update.de_json(update_data, application.bot)
            application.update_queue.put_nowait(update)
            return HttpResponse("OK", status=200)
        except Exception as e:
            logger.error(f"Telegram webhook error: {e}", exc_info=True)
            return HttpResponse("Error", status=500)
    return HttpResponse("Webhook endpoint ready", status=405)


def robots_txt(request):
    lines = [
        "User-Agent: *",
        "Disallow: /admin/",
        "Disallow: /api/",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


def health_check(request):
    return JsonResponse(
        {
            "status": "ok",
            "service": "job-bot",
            "message": "Job Bot API is running",
        }
    )


def status_page(request):
    return render(request, "status.html")

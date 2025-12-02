from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
import logging
from telegram import Update
from .telegram_bot import bot_app
from django.http import HttpResponse


logger = logging.getLogger(__name__)

@csrf_exempt
def telegram_webhook(request):
    if request.method == 'POST':
        try:
            update_data = json.loads(request.body.decode('utf-8'))
            update = Update.de_json(update_data, bot_app.bot)

            # Put update into the app's queue for async processing
            bot_app.update_queue.put_nowait(update)

            return HttpResponse("OK", status=200)
        except Exception as e:
            print(f"Error processing update: {e}")
            return HttpResponse("Error", status=500)
    return HttpResponse("Webhook called!", status=405)



@csrf_exempt
def paystack_callback(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        reference = data.get('reference')
        # Implement your callback logic here
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)



def robots_txt(request):
    lines = [
        "User-Agent: *",
        "Disallow:",
        "Sitemap: https://api.pluggedspace.org/job/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")





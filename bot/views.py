from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect
import json
import logging
from telegram import Update
from .telegram_bot import bot_app
from .utils import verify_flutterwave_payment

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
    """Handle Paystack payment callback (GET for redirect, POST for webhook)"""
    if request.method == 'GET':
        reference = request.GET.get('reference')
        # Here we can optionally verify immediately, but typically we redirect to FE
        # which will then call the /verify endpoint.
        return redirect(f'https://job.pluggedspace.org/dashboard/subscription?status=success&reference={reference}&provider=paystack')
    
    if request.method == 'POST':
        # Webhook handling logic would go here
        try:
            data = json.loads(request.body)
            reference = data.get('data', {}).get('reference')
            logger.info(f"Paystack Webhook received for reference: {reference}")
        except Exception as e:
            logger.error(f"Paystack webhook error: {e}")
            
        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error'}, status=400)


@csrf_exempt
def flutterwave_callback(request):
    """Handle Flutterwave payment callback"""
    if request.method == 'GET':
        # Redirect callback
        status = request.GET.get('status')
        tx_ref = request.GET.get('tx_ref')
        transaction_id = request.GET.get('transaction_id')
        
        if status == 'successful':
            # Verify the transaction
            result = verify_flutterwave_payment(transaction_id)
            if result.get("data", {}).get("status") == "successful":
                # Redirect to success page on frontend
                return redirect('https://job.pluggedspace.org/dashboard/subscription?status=success')
        
        return redirect('https://job.pluggedspace.org/dashboard/subscription?status=failed')
    
    return JsonResponse({'status': 'ok'})



def robots_txt(request):
    lines = [
        "User-Agent: *",
        "Disallow:",
        "Sitemap: https://api.job.pluggedspace.org/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


@csrf_exempt
def health_check(request):
    return JsonResponse({"status": "ok", "message": "Academy Backend is running!"})





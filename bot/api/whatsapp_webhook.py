"""
WhatsApp Webhook API View for Meta WhatsApp Business API
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings
import logging
import asyncio

from bot.whatsapp_bot import whatsapp_bot

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class WhatsAppWebhookView(APIView):
    """
    Webhook endpoint for Meta WhatsApp Business API
    GET: Webhook verification
    POST: Receive incoming messages
    """
    permission_classes = []  # No authentication required for webhooks
    
    def get(self, request):
        """
        Webhook verification for Meta
        Meta sends: hub.mode, hub.challenge, hub.verify_token
        """
        mode = request.GET.get('hub.mode')
        token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        
        # Check if mode and token are valid
        if mode == 'subscribe' and token == settings.META_VERIFY_TOKEN:
            logger.info("WhatsApp webhook verified successfully")
            return HttpResponse(challenge, content_type='text/plain')
        else:
            logger.warning("WhatsApp webhook verification failed")
            return Response({'error': 'Verification failed'}, status=status.HTTP_403_FORBIDDEN)
    
    def post(self, request):
        """Handle incoming WhatsApp messages from Meta"""
        try:
            body = request.data
            logger.info(f"WhatsApp webhook received: {body}")
            
            # Verify this is a WhatsApp message
            if body.get('object') != 'whatsapp_business_account':
                return Response({'status': 'ignored'}, status=status.HTTP_200_OK)
            
            # Extract message data
            for entry in body.get('entry', []):
                for change in entry.get('changes', []):
                    value = change.get('value', {})
                    
                    # Check if this is a message event
                    if 'messages' not in value:
                        continue
                    
                    messages = value.get('messages', [])
                    for message in messages:
                        # Extract message details
                        from_number = message.get('from')
                        message_type = message.get('type')
                        message_id = message.get('id')
                        
                        # Only handle text messages
                        if message_type == 'text':
                            message_body = message.get('text', {}).get('body', '')
                            
                            logger.info(f"Processing message from {from_number}: {message_body}")
                            
                            # Handle message asynchronously
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            loop.run_until_complete(
                                whatsapp_bot.handle_message(from_number, message_body, message_id)
                            )
                            loop.close()
            
            return Response({'status': 'ok'}, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"WhatsApp webhook error: {e}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

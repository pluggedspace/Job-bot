"""
Subscription and Payment API Views
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
import logging
import time

from bot.utils import create_paystack_payment, verify_paystack_payment
from bot.models import User

logger = logging.getLogger(__name__)

FREE_SEARCH_LIMIT = 10


class CreateSubscriptionView(APIView):
    """
    POST /api/subscription/create
    Body: {"email": "user@example.com"}
    
    Create a payment link for subscription
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        email = request.data.get('email', '').strip()
        
        if not email:
            # Use tenant user's email
            email = request.user.tenant_user.email
        
        if not email:
            return Response(
                {'error': 'Email is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get platform user
            tenant_user = request.user.tenant_user
            platform_users = tenant_user.platform_accounts.all()
            
            if not platform_users.exists():
                return Response(
                    {'error': 'No platform account linked. Please link a Telegram or WhatsApp account first.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            platform_user = platform_users.first()
            user_id = platform_user.user_id
            
            # Generate payment reference
            reference = f"REF_{user_id}_{int(time.time())}"
            
            # Create payment
            data = create_paystack_payment(email, 4500, reference)
            
            if not data.get("status"):
                return Response(
                    {'error': 'Error creating payment link'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Update user status to Pending
            platform_user.subscription_status = "Pending"
            platform_user.payment_reference = reference
            platform_user.save()
            
            return Response({
                'authorization_url': data['data']['authorization_url'],
                'access_code': data['data'].get('access_code'),
                'reference': reference,
                'amount': 4500,
                'currency': 'NGN'
            })
        except Exception as e:
            logger.error(f"Create subscription error: {e}", exc_info=True)
            return Response(
                {'error': 'Failed to create payment link'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VerifyPaymentView(APIView):
    """
    POST /api/subscription/verify
    Body: {"reference": "REF_123456"}
    
    Verify payment status
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        reference = request.data.get('reference', '').strip()
        
        if not reference:
            return Response(
                {'error': 'Payment reference is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get platform user
            tenant_user = request.user.tenant_user
            platform_users = tenant_user.platform_accounts.all()
            
            if not platform_users.exists():
                return Response(
                    {'error': 'No platform account linked'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            platform_user = platform_users.first()
            
            # Verify payment
            result = verify_paystack_payment(reference)
            
            if result.get("data", {}).get("status") == "success":
                platform_user.subscription_status = "Paid"
                platform_user.payment_reference = reference
                platform_user.save()
                
                return Response({
                    'success': True,
                    'message': 'Payment verified successfully! You are now a Premium user.',
                    'subscription_status': 'Paid'
                })
            else:
                return Response(
                    {
                        'success': False,
                        'message': 'Payment verification failed or still pending.'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            logger.error(f"Verify payment error: {e}", exc_info=True)
            return Response(
                {'error': 'An error occurred during verification'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class QuotaView(APIView):
    """
    GET /api/subscription/quota
    
    Get user's search quota and limits
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            tenant_user = request.user.tenant_user
            platform_users = tenant_user.platform_accounts.all()
            
            if not platform_users.exists():
                return Response(
                    {'error': 'No platform account linked'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            platform_user = platform_users.first()
            
            is_premium = platform_user.subscription_status == 'Paid'
            
            return Response({
                'subscription_status': platform_user.subscription_status,
                'is_premium': is_premium,
                'search_count': platform_user.search_count,
                'search_limit': None if is_premium else FREE_SEARCH_LIMIT,
                'searches_remaining': None if is_premium else max(0, FREE_SEARCH_LIMIT - platform_user.search_count),
                'alert_count': platform_user.alerts.filter(active=True).count(),
                'alert_limit': 5 if is_premium else 1,
                'features': {
                    'unlimited_searches': is_premium,
                    'multiple_alerts': is_premium,
                    'cv_review': is_premium,
                    'cover_letter': is_premium,
                    'interview_practice': is_premium
                }
            })
        except Exception as e:
            logger.error(f"Quota check error: {e}", exc_info=True)
            return Response(
                {'error': 'Failed to check quota'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

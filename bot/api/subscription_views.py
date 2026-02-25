"""
Subscription and Payment API Views
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
import logging
import time

from bot.utils import (
    create_paystack_payment, verify_paystack_payment,
    create_flutterwave_payment, verify_flutterwave_payment
)
from bot.models import User

logger = logging.getLogger(__name__)

FREE_SEARCH_LIMIT = 10


class CreateSubscriptionView(APIView):
    """
    POST /api/subscription/create
    Body: {
        "email": "user@example.com",
        "currency": "NGN" or "USD",  # Optional, defaults to NGN
        "provider": "paystack" or "flutterwave"  # Optional, auto-selected based on currency
    }
    
    Create a payment link for subscription
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        email = request.data.get('email', '').strip()
        currency = request.data.get('currency', 'NGN').upper()
        provider = request.data.get('provider', '').lower()
        
        # Auto-select provider based on currency if not specified
        if not provider:
            provider = 'paystack' if currency == 'NGN' else 'flutterwave'
        
        # Validate currency-provider combination
        if provider == 'paystack' and currency != 'NGN':
            return Response(
                {'error': 'Paystack only supports NGN currency'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
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
            prefix = "JOBBOT_PSTK" if provider == 'paystack' else "JOBBOT_FLW"
            reference = f"{prefix}_{user_id}_{int(time.time())}"
            
            # Create payment based on provider
            if provider == 'paystack':
                amount = 4500  # NGN
                data = create_paystack_payment(email, amount, reference)
                
                if not data.get("status"):
                    return Response(
                        {'error': 'Error creating payment link'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                
                response_data = {
                    'authorization_url': data['data']['authorization_url'],
                    'access_code': data['data'].get('access_code'),
                    'reference': reference,
                    'amount': amount,
                    'currency': 'NGN',
                    'provider': 'paystack'
                }
            
            elif provider == 'flutterwave':
                amount = 9.99 if currency == 'USD' else 4500  # USD or NGN
                data = create_flutterwave_payment(email, amount, currency, reference)
                
                if data.get("status") == "error":
                    return Response(
                        {'error': 'Error creating payment link'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                
                response_data = {
                    'authorization_url': data['data']['link'],
                    'reference': reference,
                    'amount': amount,
                    'currency': currency,
                    'provider': 'flutterwave'
                }
            
            else:
                return Response(
                    {'error': 'Invalid payment provider'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update user status to Pending
            platform_user.subscription_status = "Pending"
            platform_user.payment_reference = reference
            platform_user.save()
            
            return Response(response_data)
        except Exception as e:
            logger.error(f"Create subscription error: {e}", exc_info=True)
            return Response(
                {'error': 'Failed to create payment link'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VerifyPaymentView(APIView):
    """
    POST /api/subscription/verify
    Body: {
        "reference": "REF_123456",
        "provider": "paystack" or "flutterwave"  # Optional, auto-detected from reference
    }
    
    Verify payment status
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        reference = request.data.get('reference', '').strip()
        provider = request.data.get('provider', '').lower()
        
        if not reference:
            return Response(
                {'error': 'Payment reference is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Auto-detect provider from reference if not provided
        if not provider:
            if 'JOBBOT_PSTK_' in reference or reference.startswith('PAYSTACK_') or reference.startswith('REF_'):
                provider = 'paystack'
            elif 'JOBBOT_FLW_' in reference or reference.startswith('FLUTTERWAVE_') or reference.startswith('FLW_'):
                provider = 'flutterwave'
            else:
                # Default to paystack for backward compatibility
                provider = 'paystack'
        
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
            
            # Verify payment based on provider
            if provider == 'paystack':
                result = verify_paystack_payment(reference)
                success = result.get("data", {}).get("status") == "success"
            
            elif provider == 'flutterwave':
                result = verify_flutterwave_payment(reference)
                success = result.get("data", {}).get("status") == "successful"
            
            else:
                return Response(
                    {'error': 'Invalid payment provider'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if success:
                platform_user.subscription_status = "Paid"
                platform_user.payment_reference = reference
                platform_user.save()
                
                # Sync all data to the TenantUser immediately
                from bot.services.account_linking import AccountLinkingService
                AccountLinkingService.sync_all_data(tenant_user)
                
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
            
            # Check if ANY account is premium
            is_premium = tenant_user.subscription_status == 'Paid' or \
                         platform_users.filter(subscription_status='Paid').exists()
            
            # Use aggregated search count from TenantUser (which should be synced)
            search_count = tenant_user.search_count
            
            return Response({
                'subscription_status': 'Paid' if is_premium else 'Free',
                'is_premium': is_premium,
                'search_count': search_count,
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

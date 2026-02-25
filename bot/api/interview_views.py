"""
Interview Practice API Views
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from asgiref.sync import sync_to_async
import logging

from bot.services.interview import handle_interview_practice, cancel_session, get_active_session
from bot.models import User

logger = logging.getLogger(__name__)


class InterviewPracticeView(APIView):
    """
    POST /api/interview/practice
    Body: {"message": "user response"} or {} to start
    
    Interactive mock interview practice
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        message = request.data.get('message', '').strip()
        
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
            
            # Check subscription
            if platform_user.subscription_status != 'Paid':
                return Response(
                    {
                        'error': 'Premium feature',
                        'message': 'Interview practice is available only to Premium users. Please upgrade to access this feature.'
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Handle interview
            # Handle interview
            is_start = not message
            from asgiref.sync import async_to_sync
            result = async_to_sync(handle_interview_practice)(
                platform_user,
                None if is_start else message
            )
            
            return Response({
                'response': result,
                'is_active': True
            })
        except Exception as e:
            logger.error(f"Interview practice error: {e}", exc_info=True)
            return Response(
                {'error': 'Failed to process interview practice'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class InterviewSessionView(APIView):
    """
    GET /api/interview/session - Check active session
    DELETE /api/interview/session - Cancel/end session
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Check if there's an active interview session"""
        try:
            tenant_user = request.user.tenant_user
            platform_users = tenant_user.platform_accounts.all()
            
            if not platform_users.exists():
                return Response({'is_active': False})
            
            platform_user = platform_users.first()
            platform_user = platform_users.first()
            from asgiref.sync import async_to_sync
            active_session = async_to_sync(get_active_session)(platform_user)
            
            return Response({
                'is_active': active_session is not None,
                'session': {
                    'id': active_session.id,
                    'question_count': active_session.question_count,
                    'started_at': active_session.started_at
                } if active_session else None
            })
        except Exception as e:
            logger.error(f"Get session error: {e}", exc_info=True)
            return Response({'is_active': False})
    
    def delete(self, request):
        """Cancel/end the active interview session"""
        try:
            tenant_user = request.user.tenant_user
            platform_users = tenant_user.platform_accounts.all()
            
            if not platform_users.exists():
                return Response(
                    {'error': 'No platform account linked'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            platform_user = platform_users.first()
            platform_user = platform_users.first()
            from asgiref.sync import async_to_sync
            success = async_to_sync(cancel_session)(platform_user)
            
            if success:
                return Response({'message': 'Interview session cancelled successfully'})
            else:
                return Response(
                    {'error': 'No active session to cancel'},
                    status=status.HTTP_404_NOT_FOUND
                )
        except Exception as e:
            logger.error(f"Cancel session error: {e}", exc_info=True)
            return Response(
                {'error': 'Failed to cancel session'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

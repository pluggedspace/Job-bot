"""
CV Enhancement API Views
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
import logging

from bot.improve import review_cv, generate_cover_letter
from bot.models import User

logger = logging.getLogger(__name__)


class CVReviewView(APIView):
    """
    POST /api/cv/review
    
    Get AI-powered CV review and feedback (Premium feature)
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
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
                        'message': 'CV Review is available only to Premium users. Please upgrade to access this feature.'
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Generate CV review
            result = review_cv(platform_user)
            
            if result.get('error'):
                return Response(
                    {
                        'error': 'Incomplete profile',
                        'missing_fields': result.get('missing_fields', []),
                        'message': f"Missing profile fields: {', '.join(result.get('missing_fields', []))}. Please complete your profile first."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response({
                'cv_review': result.get('cv_review', ''),
                'success': True
            })
        except Exception as e:
            logger.error(f"CV review error: {e}", exc_info=True)
            return Response(
                {'error': 'Failed to review CV'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CoverLetterView(APIView):
    """
    POST /api/cv/coverletter
    Body: {"job_title": "Software Engineer", "company": "Google"}
    
    Generate AI-powered cover letter (Premium feature)
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        job_title = request.data.get('job_title', '').strip()
        company = request.data.get('company', '').strip()
        
        if not job_title:
            return Response(
                {'error': 'Job title is required'},
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
            
            # Check subscription
            if platform_user.subscription_status != 'Paid':
                return Response(
                    {
                        'error': 'Premium feature',
                        'message': 'Cover Letter Generator is available only to Premium users. Please upgrade to access this feature.'
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Generate cover letter
            result = generate_cover_letter(platform_user, job_title, company)
            
            if result.get('error'):
                return Response(
                    {
                        'error': 'Incomplete profile',
                        'missing_fields': result.get('missing_fields', []),
                        'message': f"Missing profile fields: {', '.join(result.get('missing_fields', []))}. Please complete your profile first."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response({
                'cover_letter': result.get('cover_letter', ''),
                'job_title': job_title,
                'company': company or 'Company',
                'success': True
            })
        except Exception as e:
            logger.error(f"Cover letter error: {e}", exc_info=True)
            return Response(
                {'error': 'Failed to generate cover letter'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

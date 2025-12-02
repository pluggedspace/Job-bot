"""
Career Growth API Views
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from asgiref.sync import sync_to_async
import logging

from bot.services.career_path import resolve_career_path
from bot.services.upskill import get_upskill_plan
from bot.models import User

logger = logging.getLogger(__name__)


class CareerPathView(APIView):
    """
    POST /api/career/path
    Body: {"role": "software engineer"}
    
    Get career progression paths for a given role
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        role = request.data.get('role', '').strip()
        
        if not role:
            # Try to get from user's profile
            tenant_user = request.user.tenant_user
            platform_users = tenant_user.platform_accounts.all()
            
            if platform_users.exists():
                platform_user = platform_users.first()
                if hasattr(platform_user, 'profile') and platform_user.profile:
                    role = platform_user.profile.current_job_title
            
            if not role:
                return Response(
                    {'error': 'Please provide a job title or create your CV first.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        try:
            data, source = resolve_career_path(role)
            
            if "error" in data:
                return Response(
                    {'error': data['error']},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response({
                'input_title': data.get('input_title', role),
                'source': source,
                'broader': data.get('broader', []),
                'narrower': data.get('narrower', []),
                'related': data.get('related', [])
            })
        except Exception as e:
            logger.error(f"Career path error: {e}", exc_info=True)
            return Response(
                {'error': 'Failed to get career path'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UpskillPlanView(APIView):
    """
    POST /api/career/upskill
    Body: {"target_role": "data scientist"}
    
    Get personalized learning plan for a target role
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        target_role = request.data.get('target_role', '').strip()
        
        if not target_role:
            return Response(
                {'error': 'Please specify a target job title or skill.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get platform user to access profile
            tenant_user = request.user.tenant_user
            platform_users = tenant_user.platform_accounts.all()
            
            if not platform_users.exists():
                return Response(
                    {'error': 'No platform account linked. Please link a Telegram or WhatsApp account first.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            platform_user = platform_users.first()
            
            # Generate upskill plan
            plan = get_upskill_plan(platform_user, target_role)
            
            if not plan or not plan.get('target'):
                return Response(
                    {'error': 'Could not generate an upskill plan. Please try a different role.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response({
                'target': plan.get('target'),
                'skills_to_gain': plan.get('skills_to_gain', []),
                'note': plan.get('note', '')
            })
        except Exception as e:
            logger.error(f"Upskill plan error: {e}", exc_info=True)
            return Response(
                {'error': 'Failed to generate upskill plan'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

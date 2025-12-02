"""
REST API Views for Job Bot
"""
from rest_framework import status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework import serializers
from django.utils import timezone

from bot.models import User, TenantUser, Job, Alert
from bot.serializers import (
    TenantUserSerializer, PlatformUserSerializer, JobSerializer,
    AlertSerializer, AccountLinkSerializer, LinkedAccountsSerializer
)
from bot.services.account_linking import AccountLinkingService
from bot.functions.jobs import get_all_jobs
import logging

logger = logging.getLogger(__name__)


class UserProfileView(APIView):
    """
    GET /api/user/profile - Get current user profile
    PATCH /api/user/profile - Update user profile
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        tenant_user = request.user.tenant_user
        serializer = TenantUserSerializer(tenant_user)
        return Response(serializer.data)
    
    def patch(self, request):
        tenant_user = request.user.tenant_user
        serializer = TenantUserSerializer(tenant_user, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LinkAccountView(APIView):
    """
    POST /api/account/link
    Body: {"link_code": "ABC123"}
    
    Link a platform account (Telegram/WhatsApp) to the current TenantUser
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = AccountLinkSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        link_code = serializer.validated_data['link_code']
        tenant_user = request.user.tenant_user
        
        # Verify and link
        success, message, platform_user = AccountLinkingService.verify_and_link(
            link_code, 
            tenant_user
        )
        
        if success:
            return Response({
                'success': True,
                'message': message,
                'platform': platform_user.platform_type,
                'username': platform_user.username,
                'linked_account': PlatformUserSerializer(platform_user).data
            })
        else:
            return Response(
                {'error': message},
                status=status.HTTP_400_BAD_REQUEST
            )


class LinkedAccountsView(APIView):
    """
    GET /api/account/linked - Get all linked platform accounts
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        tenant_user = request.user.tenant_user
        linked = AccountLinkingService.get_linked_accounts(tenant_user)
        
        serializer = LinkedAccountsSerializer(linked)
        return Response(serializer.data)


class UnlinkAccountView(APIView):
    """
    POST /api/account/unlink
    Body: {"platform": "telegram" or "whatsapp"}
    
    Unlink a platform account from the current TenantUser
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        platform_type = request.data.get('platform')
        
        if platform_type not in ['telegram', 'whatsapp']:
            return Response(
                {'error': 'Invalid platform. Must be "telegram" or "whatsapp"'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        tenant_user = request.user.tenant_user
        
        # Find the platform account
        try:
            platform_user = User.objects.get(
                tenant_user=tenant_user,
                platform_type=platform_type
            )
        except User.DoesNotExist:
            return Response(
                {'error': f'No {platform_type} account linked'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Unlink
        success = AccountLinkingService.unlink_platform_account(platform_user)
        
        if success:
            return Response({
                'success': True,
                'message': f'{platform_type.title()} account unlinked successfully'
            })
        else:
            return Response(
                {'error': 'Failed to unlink account'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class JobSearchView(APIView):
    """
    POST /api/jobs/search
    Body: {"query": "python developer", "filters": {...}}
    
    Search for jobs
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        query = request.data.get('query', '')
        filters = request.data.get('filters', {})
        
        if not query:
            return Response(
                {'error': 'Query is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        tenant_user = request.user.tenant_user
        
        # Check search limit for free users
        if tenant_user.subscription_status != 'Paid':
            if tenant_user.search_count >= 10:  # FREE_SEARCH_LIMIT
                return Response(
                    {'error': 'Search limit reached. Please upgrade to premium.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            tenant_user.search_count += 1
            tenant_user.save()
        
        # Search jobs
        try:
            jobs = get_all_jobs(query, filters)
            
            return Response({
                'query': query,
                'count': len(jobs),
                'jobs': jobs[:20],  # Limit to 20 results
                'searches_remaining': max(0, 10 - tenant_user.search_count) if tenant_user.subscription_status != 'Paid' else None
            })
        except Exception as e:
            logger.error(f"Job search error: {e}", exc_info=True)
            return Response(
                {'error': 'Failed to search jobs'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SavedJobsView(APIView):
    """
    GET /api/jobs/saved - Get saved jobs
    POST /api/jobs/saved - Save a job
    DELETE /api/jobs/saved/{id} - Remove saved job
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Get platform user linked to this tenant user
        platform_users = request.user.tenant_user.platform_accounts.all()
        
        if not platform_users.exists():
            return Response({'jobs': []})
        
        # Get jobs from all linked platform accounts
        jobs = Job.objects.filter(user__in=platform_users).order_by('-saved_at')
        serializer = JobSerializer(jobs, many=True)
        
        return Response({'jobs': serializer.data})
    
    def post(self, request):
        # Save job to the first linked platform account
        platform_users = request.user.tenant_user.platform_accounts.all()
        
        if not platform_users.exists():
            return Response(
                {'error': 'No platform account linked. Please link a Telegram or WhatsApp account first.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        platform_user = platform_users.first()
        
        serializer = JobSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=platform_user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AlertViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for job alerts
    GET /api/alerts/ - List alerts
    POST /api/alerts/ - Create alert
    PATCH /api/alerts/{id}/ - Update alert
    DELETE /api/alerts/{id}/ - Delete alert
    """
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    
    def get_queryset(self):
        # Get alerts from all linked platform accounts
        platform_users = self.request.user.tenant_user.platform_accounts.all()
        return Alert.objects.filter(user__in=platform_users).order_by('-created_at')
    
    def perform_create(self, serializer):
        # Create alert for the first linked platform account
        platform_users = self.request.user.tenant_user.platform_accounts.all()
        
        if not platform_users.exists():
            raise serializers.ValidationError(
                'No platform account linked. Please link a Telegram or WhatsApp account first.'
            )
        
        platform_user = platform_users.first()
        
        # Check alert limit
        active_count = Alert.objects.filter(user=platform_user, active=True).count()
        limit = 5 if platform_user.subscription_status == 'Paid' else 1
        
        if active_count >= limit:
            raise serializers.ValidationError(
                f'Alert limit reached. You can have up to {limit} active alert(s).'
            )
        
        serializer.save(user=platform_user)
    
    @action(detail=True, methods=['post'])
    def toggle(self, request, pk=None):
        """Toggle alert active status"""
        alert = self.get_object()
        alert.active = not alert.active
        alert.save()
        
        serializer = self.get_serializer(alert)
        return Response(serializer.data)

"""
REST API Views for Job Bot
"""
from rest_framework import status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework import serializers

from bot.models import Job, Alert
from bot.serializers import UserProfileSerializer, JobSerializer, AlertSerializer
from bot.api.helpers import get_bot_user, is_premium
from bot.functions.jobs import get_all_jobs
from bot.constants import FREE_SEARCH_LIMIT, FREE_ALERT_LIMIT, PREMIUM_ALERT_LIMIT
import logging

logger = logging.getLogger(__name__)


class UserProfileView(APIView):
    """
    GET /api/user/profile - Get current user profile
    PATCH /api/user/profile - Update user profile
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = get_bot_user(request)
        serializer = UserProfileSerializer(user)
        return Response(serializer.data)

    def patch(self, request):
        user = get_bot_user(request)
        serializer = UserProfileSerializer(user, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class JobSearchView(APIView):
    """
    POST /api/jobs/search
    Body: {"query": "python developer", "filters": {...}}
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        query = request.data.get("query", "")
        filters = request.data.get("filters", {})

        if not query:
            return Response({"error": "Query is required"}, status=status.HTTP_400_BAD_REQUEST)

        user = get_bot_user(request)
        logger.info(f"Web search request - query: '{query}', user: {user.user_id}")

        premium = is_premium(user)
        if not premium and user.search_count >= FREE_SEARCH_LIMIT:
            return Response(
                {"error": "Search limit reached. Set ENABLE_PREMIUM=true for unlimited searches."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not premium:
            user.search_count += 1
            user.save(update_fields=["search_count"])

        try:
            jobs = get_all_jobs(query, filters)
            display_limit = 50 if premium else 20

            return Response(
                {
                    "query": query,
                    "count": len(jobs),
                    "jobs": jobs[:display_limit],
                    "is_premium": premium,
                    "searches_remaining": max(0, FREE_SEARCH_LIMIT - user.search_count)
                    if not premium
                    else None,
                }
            )
        except Exception as e:
            logger.error(f"Job search error: {e}", exc_info=True)
            return Response({"error": "Failed to search jobs"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SavedJobsView(APIView):
    """
    GET /api/jobs/saved - Get saved jobs
    POST /api/jobs/saved - Save a job
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = get_bot_user(request)
        jobs = Job.objects.filter(user=user).order_by("-saved_at")
        serializer = JobSerializer(jobs, many=True)
        return Response({"jobs": serializer.data})

    def post(self, request):
        user = get_bot_user(request)
        serializer = JobSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AlertViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for job alerts.
    """

    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        user = get_bot_user(self.request)
        return Alert.objects.filter(user=user).order_by("-created_at")

    def perform_create(self, serializer):
        user = get_bot_user(self.request)
        active_count = Alert.objects.filter(user=user, active=True).count()
        limit = PREMIUM_ALERT_LIMIT if is_premium(user) else FREE_ALERT_LIMIT

        if active_count >= limit:
            raise serializers.ValidationError(
                f"Alert limit reached. You can have up to {limit} active alert(s)."
            )

        serializer.save(user=user)

    @action(detail=True, methods=["post"])
    def toggle(self, request, pk=None):
        alert = self.get_object()
        alert.active = not alert.active
        alert.save()
        serializer = self.get_serializer(alert)
        return Response(serializer.data)

"""
Subscription API Views (optional — disabled unless ENABLE_PAYMENTS=true)
"""
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
import logging

from bot.api.helpers import get_bot_user, is_premium
from bot.constants import FREE_SEARCH_LIMIT

logger = logging.getLogger(__name__)


def payments_enabled():
    return getattr(settings, "ENABLE_PAYMENTS", False)


class CreateSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not payments_enabled():
            return Response(
                {"error": "Payments are disabled in self-hosted mode. Set ENABLE_PREMIUM=true instead."},
                status=status.HTTP_501_NOT_IMPLEMENTED,
            )
        return Response({"error": "Payment provider not configured"}, status=status.HTTP_501_NOT_IMPLEMENTED)


class VerifyPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not payments_enabled():
            return Response(
                {"error": "Payments are disabled in self-hosted mode."},
                status=status.HTTP_501_NOT_IMPLEMENTED,
            )
        return Response({"error": "Payment provider not configured"}, status=status.HTTP_501_NOT_IMPLEMENTED)


class QuotaView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = get_bot_user(request)
        premium = is_premium(user)
        return Response(
            {
                "subscription_status": "Paid" if premium else user.subscription_status,
                "is_premium": premium,
                "search_count": user.search_count,
                "searches_remaining": None if premium else max(0, FREE_SEARCH_LIMIT - user.search_count),
            }
        )

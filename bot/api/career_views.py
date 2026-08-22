"""
Career Growth API Views
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
import logging

from bot.services.career_path import resolve_career_path
from bot.services.upskill import get_upskill_plan
from bot.api.helpers import get_bot_user

logger = logging.getLogger(__name__)


class CareerPathView(APIView):
    """
    POST /api/career/path
    Body: {"role": "software engineer"}
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        role = request.data.get("role", "").strip()

        if not role:
            user = get_bot_user(request)
            role = user.current_job_title or ""
            if not role:
                return Response(
                    {"error": "Please provide a job title or set current_job_title on your profile."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        try:
            data, source = resolve_career_path(role)

            if "error" in data:
                return Response({"error": data["error"]}, status=status.HTTP_400_BAD_REQUEST)

            return Response({"role": role, "career_path": data, "source": source})
        except Exception as e:
            logger.error(f"Career path error: {e}", exc_info=True)
            return Response(
                {"error": "Failed to resolve career path"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UpskillPlanView(APIView):
    """
    POST /api/career/upskill
    Body: {"current_role": "...", "target_role": "..."}
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        current_role = request.data.get("current_role", "").strip()
        target_role = request.data.get("target_role", "").strip()

        if not current_role or not target_role:
            user = get_bot_user(request)
            current_role = current_role or user.current_job_title or ""
            if not current_role or not target_role:
                return Response(
                    {"error": "Both current_role and target_role are required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        try:
            plan = get_upskill_plan(current_role, target_role)
            return Response({"current_role": current_role, "target_role": target_role, "plan": plan})
        except Exception as e:
            logger.error(f"Upskill plan error: {e}", exc_info=True)
            return Response(
                {"error": "Failed to generate upskill plan"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

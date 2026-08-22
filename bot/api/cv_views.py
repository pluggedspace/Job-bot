"""
CV Enhancement API Views
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
import logging

from bot.improve import review_cv, generate_cover_letter
from bot.api.helpers import get_bot_user, is_premium

logger = logging.getLogger(__name__)


class CVReviewView(APIView):
    """
    POST /api/cv/review
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = get_bot_user(request)

        if not is_premium(user):
            return Response(
                {
                    "error": "Premium feature",
                    "message": "Set ENABLE_PREMIUM=true to use CV review in self-hosted mode.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            result = review_cv(user)

            if result.get("error"):
                return Response(
                    {
                        "error": "Incomplete profile",
                        "missing_fields": result.get("missing_fields", []),
                        "message": f"Missing profile fields: {', '.join(result.get('missing_fields', []))}.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            return Response({"cv_review": result.get("cv_review", ""), "success": True})
        except Exception as e:
            logger.error(f"CV review error: {e}", exc_info=True)
            return Response({"error": "Failed to review CV"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CoverLetterView(APIView):
    """
    POST /api/cv/coverletter
    Body: {"job_title": "Software Engineer", "company": "Google"}
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        job_title = request.data.get("job_title", "").strip()
        company = request.data.get("company", "").strip()

        if not job_title:
            return Response({"error": "Job title is required"}, status=status.HTTP_400_BAD_REQUEST)

        user = get_bot_user(request)
        if not is_premium(user):
            return Response(
                {
                    "error": "Premium feature",
                    "message": "Set ENABLE_PREMIUM=true to use cover letter generation in self-hosted mode.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            result = generate_cover_letter(user, job_title, company)

            if result.get("error"):
                return Response(
                    {
                        "error": "Incomplete profile",
                        "missing_fields": result.get("missing_fields", []),
                        "message": f"Missing profile fields: {', '.join(result.get('missing_fields', []))}.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            return Response(
                {
                    "cover_letter": result.get("cover_letter", ""),
                    "job_title": job_title,
                    "company": company or "Company",
                    "success": True,
                }
            )
        except Exception as e:
            logger.error(f"Cover letter error: {e}", exc_info=True)
            return Response(
                {"error": "Failed to generate cover letter"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

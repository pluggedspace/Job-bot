"""
Interview Practice API Views
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from asgiref.sync import async_to_sync
import logging

from bot.services.interview import handle_interview_practice, cancel_session, get_active_session
from bot.api.helpers import get_bot_user, is_premium

logger = logging.getLogger(__name__)


class InterviewPracticeView(APIView):
    """
    POST /api/interview/practice
    Body: {"message": "user response"} or {} to start
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        message = request.data.get("message", "").strip()
        user = get_bot_user(request)

        if not is_premium(user):
            return Response(
                {
                    "error": "Premium feature",
                    "message": "Set ENABLE_PREMIUM=true to use interview practice in self-hosted mode.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            result = async_to_sync(handle_interview_practice)(user, None if not message else message)
            return Response({"response": result, "is_active": True})
        except Exception as e:
            logger.error(f"Interview practice error: {e}", exc_info=True)
            return Response(
                {"error": "Failed to process interview practice"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class InterviewSessionView(APIView):
    """
    GET /api/interview/session - Check active session
    DELETE /api/interview/session - Cancel/end session
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = get_bot_user(request)
        try:
            active_session = async_to_sync(get_active_session)(user)
            return Response(
                {
                    "is_active": active_session is not None,
                    "session": {
                        "id": active_session.id,
                        "question_count": active_session.current_question,
                        "started_at": active_session.started_at,
                    }
                    if active_session
                    else None,
                }
            )
        except Exception as e:
            logger.error(f"Get session error: {e}", exc_info=True)
            return Response({"is_active": False})

    def delete(self, request):
        user = get_bot_user(request)
        try:
            success = async_to_sync(cancel_session)(user)
            if success:
                return Response({"message": "Interview session cancelled successfully"})
            return Response({"error": "No active session to cancel"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Cancel session error: {e}", exc_info=True)
            return Response({"error": "Failed to cancel session"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

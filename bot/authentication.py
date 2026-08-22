import logging

from django.conf import settings
from rest_framework import authentication, exceptions

from .models import User

logger = logging.getLogger(__name__)


class APITokenUser:
    """Authenticated API user wrapper around the single bot User record."""

    def __init__(self, bot_user):
        self.bot_user = bot_user
        self.id = bot_user.user_id
        self.email = bot_user.email or ""
        self.username = bot_user.username or "owner"
        self.full_name = bot_user.full_name or ""
        self.is_authenticated = True
        self.is_active = True
        self.pk = bot_user.pk

    def __str__(self):
        return self.email or self.username


class APITokenAuthentication(authentication.BaseAuthentication):
    """Validate a static API token from the environment (self-hosted single user)."""

    def authenticate(self, request):
        api_token = getattr(settings, "API_TOKEN", None)
        if not api_token:
            logger.warning("API_TOKEN is not configured; API authentication is disabled")
            return None

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split("Bearer ", 1)[1].strip()
        if token != api_token:
            raise exceptions.AuthenticationFailed("Invalid API token")

        bot_user = User.get_default_user()
        return (APITokenUser(bot_user), None)

    def authenticate_header(self, request):
        return 'Bearer realm="api"'

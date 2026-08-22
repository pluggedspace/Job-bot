from django.conf import settings


def get_bot_user(request):
    """Return the underlying bot User model for an authenticated API request."""
    user = request.user
    if hasattr(user, "bot_user"):
        return user.bot_user
    return user


def is_premium(user):
    """Self-hosted installs can enable all features via ENABLE_PREMIUM."""
    if getattr(settings, "ENABLE_PREMIUM", True):
        return True
    return user.subscription_status == "Paid"

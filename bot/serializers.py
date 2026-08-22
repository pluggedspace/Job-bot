"""
Serializers for Job Bot API
"""
from rest_framework import serializers
from bot.models import User, Job, Alert


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for the single user profile."""

    is_premium = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "user_id",
            "email",
            "full_name",
            "username",
            "platform_type",
            "subscription_status",
            "is_premium",
            "search_count",
            "current_job_title",
            "skills",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user_id", "created_at", "updated_at"]

    def get_is_premium(self, obj):
        from bot.api.helpers import is_premium

        return is_premium(obj)


class JobSerializer(serializers.ModelSerializer):
    """Serializer for saved jobs."""

    class Meta:
        model = Job
        fields = ["id", "job_id", "title", "company", "saved_at"]
        read_only_fields = ["id", "saved_at"]


class AlertSerializer(serializers.ModelSerializer):
    """Serializer for job alerts."""

    class Meta:
        model = Alert
        fields = ["id", "query", "active", "created_at"]
        read_only_fields = ["id", "created_at"]

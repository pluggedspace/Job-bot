from django.db import models
from django.utils.text import slugify


class User(models.Model):
    """Single-user profile for Telegram, WhatsApp, and API access."""

    user_id = models.CharField(max_length=100, unique=True)
    username = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    full_name = models.CharField(max_length=255, null=True, blank=True)

    telegram_id = models.CharField(max_length=100, null=True, blank=True, unique=True)
    whatsapp_id = models.CharField(max_length=100, null=True, blank=True, unique=True)
    platform_type = models.CharField(
        max_length=20,
        choices=[
            ("telegram", "Telegram"),
            ("whatsapp", "WhatsApp"),
            ("api", "API"),
        ],
        default="telegram",
    )

    subscription_status = models.CharField(max_length=20, default="Free")
    payment_reference = models.CharField(max_length=100, null=True, blank=True)
    search_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    cv_data = models.JSONField(null=True, blank=True)
    current_job_title = models.CharField(max_length=255, null=True, blank=True)
    skills = models.JSONField(default=list, blank=True)

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        label = self.username or self.email or "Unknown"
        return f"{label} ({self.platform_type}: {self.user_id})"

    @classmethod
    def get_default_user(cls):
        user, _ = cls.objects.get_or_create(
            user_id="default",
            defaults={
                "username": "owner",
                "platform_type": "api",
            },
        )
        return user


class Job(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="jobs")
    job_id = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Job"
        verbose_name_plural = "Jobs"
        ordering = ["-saved_at"]

    def __str__(self):
        return f"{self.title} at {self.company}"


class Alert(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="alerts")
    query = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Alert"
        verbose_name_plural = "Alerts"

    def __str__(self):
        return f"Alert for '{self.query}'"


class CareerPathCache(models.Model):
    input_title = models.CharField(max_length=255, unique=True)
    normalized_title = models.SlugField(max_length=255, unique=True)
    result_data = models.JSONField()
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.normalized_title:
            self.normalized_title = slugify(self.input_title)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Cached Path: {self.input_title}"


class InterviewSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    job_title = models.CharField(max_length=255)
    started_at = models.DateTimeField(auto_now_add=True)
    is_complete = models.BooleanField(default=False)
    current_question = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=5)


class InterviewResponse(models.Model):
    session = models.ForeignKey(InterviewSession, on_delete=models.CASCADE)
    question = models.TextField()
    answer = models.TextField()
    is_follow_up = models.BooleanField(default=False)

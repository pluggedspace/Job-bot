from django.db import models

class User(models.Model):
    user_id = models.CharField(max_length=100, unique=True)
    username = models.CharField(max_length=100, null=True, blank=True)
    subscription_status = models.CharField(max_length=20, default='Free')
    payment_reference = models.CharField(max_length=100, null=True, blank=True)
    search_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return f"{self.username} ({self.user_id})"

class Job(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='jobs')
    job_id = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Job"
        verbose_name_plural = "Jobs"
        ordering = ['-saved_at']

    def __str__(self):
        return f"{self.title} at {self.company}"

class Alert(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='alerts')
    query = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Alert"
        verbose_name_plural = "Alerts"

    def __str__(self):
        return f"Alert for '{self.query}'"
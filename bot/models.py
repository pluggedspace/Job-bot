from django.db import models
from django.utils.text import slugify
from django.utils import timezone

# Multi-tenant models for JWT authentication
class Tenant(models.Model):
    """Organization/Tenant model for multi-tenant architecture"""
    id = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Tenant"
        verbose_name_plural = "Tenants"
    
    def __str__(self):
        return self.name


class TenantUser(models.Model):
    """Main user model for JWT-authenticated users (web, API)"""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='users')
    user_id = models.CharField(max_length=100)  # From JWT 'sub' claim
    email = models.EmailField()
    full_name = models.CharField(max_length=255, null=True, blank=True)
    role = models.CharField(
        max_length=20,
        choices=[
            ('owner', 'Owner'),
            ('admin', 'Admin'),
            ('member', 'Member'),
        ],
        default='member'
    )
    
    # Job bot specific fields
    subscription_status = models.CharField(max_length=20, default='Free')
    payment_reference = models.CharField(max_length=100, null=True, blank=True)
    search_count = models.IntegerField(default=0)
    cv_data = models.JSONField(null=True, blank=True)
    current_job_title = models.CharField(max_length=255, null=True, blank=True)
    skills = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = [['tenant', 'user_id']]
        verbose_name = "Tenant User"
        verbose_name_plural = "Tenant Users"
    
    @classmethod
    def get_or_create_from_jwt(cls, tenant_id, user_id, email, full_name=None):
        """Create or update user from JWT payload"""
        tenant, _ = Tenant.objects.get_or_create(
            id=tenant_id,
            defaults={'name': tenant_id}
        )
        user, created = cls.objects.get_or_create(
            tenant=tenant,
            user_id=user_id,
            defaults={
                'email': email,
                'full_name': full_name,
            }
        )
        if not created and email:
            user.email = email
            user.full_name = full_name or user.full_name
            user.save()
        return user
    
    def __str__(self):
        return f"{self.email} @ {self.tenant.name}"


class User(models.Model):
    """Legacy user model for Telegram/WhatsApp (backward compatibility)"""
    user_id = models.CharField(max_length=100, unique=True)  # Telegram user ID
    username = models.CharField(max_length=100, null=True, blank=True)
    
    # Link to TenantUser for unified profile
    tenant_user = models.ForeignKey(
        TenantUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='platform_accounts',
        help_text="Link to unified tenant user profile"
    )
    
    # Platform identifiers for linking
    telegram_id = models.CharField(max_length=100, null=True, blank=True, unique=True)
    whatsapp_id = models.CharField(max_length=100, null=True, blank=True, unique=True)
    platform_type = models.CharField(
        max_length=20,
        choices=[
            ('telegram', 'Telegram'),
            ('whatsapp', 'WhatsApp'),
        ],
        default='telegram'
    )
    
    # Keep existing fields for backward compatibility
    subscription_status = models.CharField(max_length=20, default='Free')
    payment_reference = models.CharField(max_length=100, null=True, blank=True)
    search_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    cv_data = models.JSONField(null=True, blank=True)
    current_job_title = models.CharField(max_length=255, null=True, blank=True)
    skills = models.JSONField(default=list, blank=True)
    
    # Linking verification
    link_code = models.CharField(max_length=10, null=True, blank=True, help_text="Code to link account")
    link_code_expires = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Platform User"
        verbose_name_plural = "Platform Users"

    def __str__(self):
        return f"{self.username or 'Unknown'} ({self.platform_type}: {self.user_id})"
    
    def generate_link_code(self):
        """Generate a code for linking to TenantUser"""
        import random
        import string
        from datetime import timedelta
        
        self.link_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        self.link_code_expires = timezone.now() + timedelta(minutes=15)
        self.save()
        return self.link_code
    
    def link_to_tenant_user(self, tenant_user):
        """Link this platform account to a TenantUser"""
        self.tenant_user = tenant_user
        self.link_code = None
        self.link_code_expires = None
        self.save()
        return True

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

class CareerPathCache(models.Model):
    input_title = models.CharField(max_length=255, unique=True)  # Original input
    normalized_title = models.SlugField(max_length=255, unique=True)  # slugified for lookups
    result_data = models.JSONField()  # Stores ESCO response or structured career path
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
    is_follow_up = models.BooleanField(default=False)  # ✅ Add this line
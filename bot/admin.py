from django.contrib import admin
from .models import User, Job, Alert

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'username', 'subscription_status', 'search_count', 'created_at', 'updated_at')
    search_fields = ('user_id', 'username', 'payment_reference')
    list_filter = ('subscription_status',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('job_id', 'title', 'company', 'user', 'saved_at')
    search_fields = ('job_id', 'title', 'company', 'user__username', 'user__user_id')
    list_filter = ('company',)
    readonly_fields = ('saved_at',)

@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('query', 'user', 'active', 'created_at')
    search_fields = ('query', 'user__username', 'user__user_id')
    list_filter = ('active',)
    readonly_fields = ('created_at',)

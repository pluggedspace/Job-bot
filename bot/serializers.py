"""
Serializers for Job Bot API
"""
from rest_framework import serializers
from bot.models import User, TenantUser, Job, Alert


class TenantUserSerializer(serializers.ModelSerializer):
    """Serializer for TenantUser (web users)"""
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    is_premium = serializers.SerializerMethodField()
    
    class Meta:
        model = TenantUser
        fields = [
            'id', 'user_id', 'email', 'full_name', 'role',
            'tenant_name', 'subscription_status', 'is_premium', 'search_count',
            'current_job_title', 'skills', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user_id', 'created_at', 'updated_at']

    def get_is_premium(self, obj):
        web_paid = obj.subscription_status == 'Paid'
        linked_paid = obj.platform_accounts.filter(subscription_status='Paid').exists()
        is_premium = web_paid or linked_paid
        
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"DEBUG: Serializer checking premium for {obj.email}: web={web_paid}, linked={linked_paid}, final={is_premium}")
        
        return is_premium

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if data.get('is_premium'):
            data['subscription_status'] = 'Paid'
        return data


class PlatformUserSerializer(serializers.ModelSerializer):
    """Serializer for platform users (Telegram/WhatsApp)"""
    
    class Meta:
        model = User
        fields = [
            'id', 'user_id', 'username', 'platform_type',
            'telegram_id', 'whatsapp_id', 'subscription_status',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class JobSerializer(serializers.ModelSerializer):
    """Serializer for saved jobs"""
    
    class Meta:
        model = Job
        fields = ['id', 'job_id', 'title', 'company', 'saved_at']
        read_only_fields = ['id', 'saved_at']


class AlertSerializer(serializers.ModelSerializer):
    """Serializer for job alerts"""
    
    class Meta:
        model = Alert
        fields = ['id', 'query', 'active', 'created_at']
        read_only_fields = ['id', 'created_at']


class AccountLinkSerializer(serializers.Serializer):
    """Serializer for account linking request"""
    link_code = serializers.CharField(max_length=10, required=True)


class LinkedAccountsSerializer(serializers.Serializer):
    """Serializer for linked accounts response"""
    telegram = serializers.DictField(allow_null=True)
    whatsapp = serializers.DictField(allow_null=True)

"""
Account Linking Service for Multi-Platform Job Bot

This service allows users to link their Telegram/WhatsApp accounts
to their TenantUser profile (JWT-authenticated web users).
"""

from bot.models import User, TenantUser
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class AccountLinkingService:
    """Service to link platform accounts (Telegram/WhatsApp) to TenantUser"""
    
    @staticmethod
    def generate_link_code(platform_user):
        """
        Generate a 6-digit code for linking account
        
        Args:
            platform_user: User instance (Telegram/WhatsApp)
        
        Returns:
            str: 6-digit linking code
        """
        code = platform_user.generate_link_code()
        logger.info(f"Generated link code for {platform_user.platform_type} user {platform_user.user_id}")
        return code
    
    @staticmethod
    def verify_and_link(link_code, tenant_user):
        """
        Verify link code and link platform account to TenantUser
        
        Args:
            link_code: 6-digit code from platform user
            tenant_user: TenantUser instance to link to
        
        Returns:
            tuple: (success: bool, message: str, platform_user: User or None)
        """
        try:
            # Find user with this link code
            platform_user = User.objects.filter(
                link_code=link_code,
                link_code_expires__gt=timezone.now()
            ).first()
            
            if not platform_user:
                return False, "Invalid or expired link code", None
            
            # Check if already linked
            if platform_user.tenant_user:
                return False, f"This {platform_user.platform_type} account is already linked", None
            
            # Link the accounts
            platform_user.link_to_tenant_user(tenant_user)
            
            # Synchronize data from platform to web (if platform is Paid/has data)
            # This ensures "real data" from the bot is reflected on the web dashboard
            if platform_user.subscription_status == 'Paid':
                tenant_user.subscription_status = 'Paid'
            
            # Sync counts and profile if web is empty
            tenant_user.search_count = max(tenant_user.search_count, platform_user.search_count)
            
            if not tenant_user.cv_data and platform_user.cv_data:
                tenant_user.cv_data = platform_user.cv_data
            
            if not tenant_user.skills and platform_user.skills:
                tenant_user.skills = platform_user.skills
            
            if not tenant_user.current_job_title and platform_user.current_job_title:
                tenant_user.current_job_title = platform_user.current_job_title
                
            tenant_user.save()
            
            logger.info(
                f"Linked {platform_user.platform_type} account {platform_user.user_id} "
                f"to TenantUser {tenant_user.email} and synchronized data"
            )
            
            return True, f"Successfully linked {platform_user.platform_type} account!", platform_user
            
        except Exception as e:
            logger.error(f"Error linking accounts: {e}", exc_info=True)
            return False, "An error occurred while linking accounts", None
    
    @staticmethod
    def unlink_platform_account(platform_user):
        """
        Unlink a platform account from TenantUser
        
        Args:
            platform_user: User instance to unlink
        
        Returns:
            bool: Success status
        """
        if not platform_user.tenant_user:
            return False
        
        tenant_user_email = platform_user.tenant_user.email
        platform_user.tenant_user = None
        platform_user.save()
        
        logger.info(
            f"Unlinked {platform_user.platform_type} account {platform_user.user_id} "
            f"from TenantUser {tenant_user_email}"
        )
        
        return True
    
    @staticmethod
    def get_linked_accounts(tenant_user):
        """
        Get all platform accounts linked to a TenantUser
        
        Args:
            tenant_user: TenantUser instance
        
        Returns:
            dict: Dictionary with platform types as keys
        """
        linked = {
            'telegram': None,
            'whatsapp': None,
        }
        
        for platform_account in tenant_user.platform_accounts.all():
            linked[platform_account.platform_type] = {
                'user_id': platform_account.user_id,
                'username': platform_account.username,
                'linked_at': platform_account.updated_at,
            }
        
        return linked
    
    @staticmethod
    def sync_subscription_status(platform_user):
        """
        Sync subscription status between platform user and tenant user
        
        Args:
            platform_user: User instance
        """
        if not platform_user.tenant_user:
            return
        
        tenant_user = platform_user.tenant_user
        
        # Sync BOTH WAYS - if either is Paid, both become Paid
        if tenant_user.subscription_status == 'Paid' or platform_user.subscription_status == 'Paid':
            tenant_user.subscription_status = 'Paid'
            platform_user.subscription_status = 'Paid'
            tenant_user.save()
            platform_user.save()
        
        logger.info(
            f"Synced subscription status for {platform_user.platform_type} "
            f"user {platform_user.user_id}"
        )

    @staticmethod
    def sync_all_data(tenant_user):
        """
        Synchronize data across all linked accounts for a TenantUser
        """
        linked_accounts = tenant_user.platform_accounts.all()
        if not linked_accounts.exists():
            return
            
        # If any account is Paid, all are Paid
        any_paid = tenant_user.subscription_status == 'Paid' or \
                   linked_accounts.filter(subscription_status='Paid').exists()
        
        if any_paid:
            tenant_user.subscription_status = 'Paid'
            tenant_user.save()
            for acc in linked_accounts:
                if acc.subscription_status != 'Paid':
                    acc.subscription_status = 'Paid'
                    acc.save()
        
        # Aggregate search counts (max)
        max_searches = tenant_user.search_count
        for acc in linked_accounts:
            max_searches = max(max_searches, acc.search_count)
        
        if tenant_user.search_count != max_searches:
            tenant_user.search_count = max_searches
            tenant_user.save()
            
        logger.info(f"Synchronized all data for TenantUser {tenant_user.email}")


# Example usage in Telegram bot command
"""
async def link_account_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    '''
    /link - Generate a code to link Telegram account to web profile
    '''
    user_id = str(update.effective_user.id)
    
    # Get or create platform user
    platform_user, _ = await sync_to_async(User.objects.get_or_create)(
        telegram_id=user_id,
        defaults={
            'user_id': user_id,
            'username': update.effective_user.username,
            'platform_type': 'telegram'
        }
    )
    
    # Check if already linked
    if platform_user.tenant_user:
        await update.message.reply_text(
            f"✅ Your Telegram account is already linked to {platform_user.tenant_user.email}\\n\\n"
            "Use /unlink to disconnect."
        )
        return
    
    # Generate link code
    code = await sync_to_async(AccountLinkingService.generate_link_code)(platform_user)
    
    await update.message.reply_text(
        f"🔗 *Link Your Account*\\n\\n"
        f"Your linking code: `{code}`\\n\\n"
        f"This code expires in 15 minutes.\\n\\n"
        f"To link your account:\\n"
        f"1. Go to https://yourapp.com/settings/link\\n"
        f"2. Enter this code\\n"
        f"3. Your Telegram and web accounts will be linked!\\n\\n"
        f"Benefits:\\n"
        f"• Unified job alerts across platforms\\n"
        f"• Shared subscription status\\n"
        f"• Access your data from web or Telegram",
        parse_mode=ParseMode.MARKDOWN
    )
"""

# Example usage in Django REST API view
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class LinkAccountView(APIView):
    '''
    POST /api/account/link
    Body: {"link_code": "ABC123"}
    '''
    
    def post(self, request):
        link_code = request.data.get('link_code')
        
        if not link_code:
            return Response(
                {'error': 'Link code is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get TenantUser from JWT auth
        tenant_user = request.user.tenant_user
        
        # Verify and link
        success, message, platform_user = AccountLinkingService.verify_and_link(
            link_code, 
            tenant_user
        )
        
        if success:
            return Response({
                'success': True,
                'message': message,
                'platform': platform_user.platform_type,
                'username': platform_user.username,
            })
        else:
            return Response(
                {'error': message},
                status=status.HTTP_400_BAD_REQUEST
            )

class LinkedAccountsView(APIView):
    '''
    GET /api/account/linked
    '''
    
    def get(self, request):
        tenant_user = request.user.tenant_user
        linked = AccountLinkingService.get_linked_accounts(tenant_user)
        
        return Response({
            'linked_accounts': linked
        })
"""

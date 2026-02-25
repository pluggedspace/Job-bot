from django.test import TestCase
from bot.models import Tenant, TenantUser, User
from bot.services.account_linking import AccountLinkingService

class AccountLinkingTest(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(id="test-tenant", name="Test Tenant")
        self.web_user = TenantUser.objects.create(
            tenant=self.tenant,
            user_id="web-user-1",
            email="web@example.com",
            subscription_status="Free",
            search_count=0
        )
        self.platform_user = User.objects.create(
            user_id="platform-user-1",
            username="botuser",
            platform_type="telegram",
            subscription_status="Paid",
            search_count=5
        )
        self.platform_user.generate_link_code()

    def test_sync_on_link(self):
        """Test that data syncs from platform to web upon linking"""
        code = self.platform_user.link_code
        success, message, user = AccountLinkingService.verify_and_link(code, self.web_user)
        
        self.assertTrue(success)
        self.web_user.refresh_from_db()
        
        # Web user should be Paid and have search count synced
        self.assertEqual(self.web_user.subscription_status, "Paid")
        self.assertEqual(self.web_user.search_count, 5)

    def test_sync_both_ways(self):
        """Test that subscription status syncs both ways"""
        self.platform_user.tenant_user = self.web_user
        self.platform_user.save()
        
        # Set web user to Paid
        self.web_user.subscription_status = "Paid"
        self.web_user.save()
        
        self.platform_user.subscription_status = "Free"
        self.platform_user.save()
        
        AccountLinkingService.sync_subscription_status(self.platform_user)
        
        self.platform_user.refresh_from_db()
        self.assertEqual(self.platform_user.subscription_status, "Paid")

    def test_sync_all_data(self):
        """Test bulk synchronization across multiple platforms"""
        self.platform_user.tenant_user = self.web_user
        self.platform_user.save()
        
        whatsapp_user = User.objects.create(
            user_id="wa-1",
            platform_type="whatsapp",
            tenant_user=self.web_user,
            subscription_status="Free",
            search_count=10
        )
        
        AccountLinkingService.sync_all_data(self.web_user)
        
        self.web_user.refresh_from_db()
        whatsapp_user.refresh_from_db()
        
        self.assertEqual(self.web_user.subscription_status, "Paid")
        self.assertEqual(whatsapp_user.subscription_status, "Paid")
        self.assertEqual(self.web_user.search_count, 10)

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobsearchbot.settings')
django.setup()

from bot.models import TenantUser, User
from bot.serializers import TenantUserSerializer

def test_runtime_logic(email):
    print(f"\n--- Testing Runtime Logic for: {email} ---")
    try:
        tu = TenantUser.objects.get(email=email)
        print(f"TenantUser ID: {tu.id}, Status: {tu.subscription_status}")
        
        # Test 1: platform_accounts relation
        platform_accounts = tu.platform_accounts.all()
        print(f"Platform accounts count: {platform_accounts.count()}")
        for acc in platform_accounts:
            print(f"- {acc.platform_type} (ID: {acc.user_id}): {acc.subscription_status}")
            
        # Test 2: filter().exists() logic
        is_premium_via_linked = tu.platform_accounts.filter(subscription_status='Paid').exists()
        print(f"is_premium_via_linked (filter().exists()): {is_premium_via_linked}")
        
        # Test 3: Serializer logic
        serializer = TenantUserSerializer(tu)
        is_premium_serializer = serializer.data.get('is_premium')
        status_serializer = serializer.data.get('subscription_status')
        print(f"Serializer is_premium: {is_premium_serializer}")
        print(f"Serializer subscription_status: {status_serializer}")
        
    except TenantUser.DoesNotExist:
        print("TenantUser not found.")

if __name__ == "__main__":
    import sys
    email = sys.argv[1] if len(sys.argv) > 1 else 'cesar@pluggedspace.org'
    test_runtime_logic(email)

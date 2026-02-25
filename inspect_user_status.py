import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobsearchbot.settings')
django.setup()

from bot.models import TenantUser, User

def inspect_user(email):
    print(f"\n--- Inspecting User: {email} ---")
    try:
        tu = TenantUser.objects.get(email=email)
        print(f"TenantUser ID: {tu.id}")
        print(f"User ID: {tu.user_id}")
        print(f"Subscription Status: {tu.subscription_status}")
        print(f"Search Count: {tu.search_count}")
        print(f"Role: {tu.role}")
        
        linked = tu.platform_accounts.all()
        print(f"\nLinked Platform Accounts: {linked.count()}")
        for acc in linked:
            print(f"- Platform: {acc.platform_type}")
            print(f"  User ID: {acc.user_id}")
            print(f"  Status: {acc.subscription_status}")
            print(f"  Search Count: {acc.search_count}")
            
        # Check overall premium status as the view does
        is_premium = tu.subscription_status == 'Paid' or \
                     linked.filter(subscription_status='Paid').exists()
        print(f"\nCalculated is_premium: {is_premium}")
        
    except TenantUser.DoesNotExist:
        print("TenantUser not found.")

if __name__ == "__main__":
    import sys
    email = sys.argv[1] if len(sys.argv) > 1 else 'cesar@pluggedspace.org'
    inspect_user(email)

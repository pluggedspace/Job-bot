import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobsearchbot.settings')
django.setup()

from bot.models import TenantUser, User
from bot.services.account_linking import AccountLinkingService

def sync_all_users():
    print("\n--- Synchronizing All Users ---")
    users = TenantUser.objects.all()
    count = 0
    fixed = 0
    
    for tu in users:
        count += 1
        print(f"Checking {tu.email}...")
        
        # Check if any linked account is paid
        linked_paid = tu.platform_accounts.filter(subscription_status='Paid').exists()
        
        if linked_paid and tu.subscription_status != 'Paid':
            print(f"  Updating {tu.email} to Paid status (found linked paid account)")
            tu.subscription_status = 'Paid'
            tu.save()
            fixed += 1
            
        # Also run the full sync service method to be sure
        AccountLinkingService.sync_all_data(tu)
    
    print(f"\nFinished. Total users checked: {count}, Users fixed: {fixed}")

if __name__ == "__main__":
    sync_all_users()

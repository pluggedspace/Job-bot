import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobsearchbot.settings')
django.setup()

print("Attempting to import bot.tasks...")
try:
    from bot import tasks
    print("SUCCESS: bot.tasks imported.")
    print(f"Tasks found: {dir(tasks)}")
    
    from celery import current_app
    print(f"Registered Celery Tasks: {list(current_app.tasks.keys())}")
    
    if 'bot.tasks.check_alerts' in current_app.tasks:
        print("SUCCESS: 'bot.tasks.check_alerts' is registered in Celery.")
    else:
        print("FAILURE: 'bot.tasks.check_alerts' is NOT registered in Celery.")
        
except ImportError as e:
    print(f"FAILURE: ImportError during import: {e}")
except Exception as e:
    print(f"FAILURE: Exception during import: {e}")

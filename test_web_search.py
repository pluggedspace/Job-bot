import os
import django
import sys

# Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobsearchbot.settings')
django.setup()

from bot.functions.jobs import get_all_jobs
import logging

# Configure logging to see the output
logging.basicConfig(level=logging.INFO)

def test_search(query):
    print(f"\n--- Testing Search for: '{query}' ---")
    jobs = get_all_jobs(query)
    print(f"Total jobs found: {len(jobs)}")
    if jobs:
        print(f"First job: {jobs[0]['job_title']} at {jobs[0]['employer_name']} (Source: {jobs[0]['source']})")
    else:
        print("No jobs found.")

if __name__ == "__main__":
    test_search("Python")
    test_search("Developer")
    test_search("NonExistentJob12345")

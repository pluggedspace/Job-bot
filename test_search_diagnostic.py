import os
import django
import logging
import sys

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobsearchbot.settings')
django.setup()

from bot.functions.jobs import get_all_jobs

# Configure logging to see the output
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')

def test_search(query):
    print(f"\n--- Testing Search for: '{query}' ---")
    jobs = get_all_jobs(query)
    
    for i, job in enumerate(jobs[:3]):
        print(f"\nResult {i+1}:")
        print(f"Title: {job.get('job_title')}")
        print(f"Company: {job.get('employer_name')}")
        print(f"Source: {job.get('source', 'Unknown')}")
    
    print(f"\nTotal jobs found: {len(jobs)}")
    
    if len(jobs) == 0:
        print("\nPossible reasons for no results:")
        print("1. RapidAPI key invalid or limit reached (check logs)")
        print("2. Keywords might be too specific (though word-matching is now enabled)")
        print("3. Network connectivity issues within container")

if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "Python Developer"
    test_search(query)

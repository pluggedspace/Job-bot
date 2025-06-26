import requests
import logging
from django.conf import settings
import datetime

logger = logging.getLogger(__name__)

# Paystack Utils
def create_paystack_payment(email: str, amount: int, reference: str = None) -> dict:
    url = "https://api.paystack.co/transaction/initialize"
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "email": email,
        "amount": amount * 100,
        "callback_url": "https://yourdomain.com/callback/"
    }
    if reference:
        data["trxref"] = reference
    try:
        response = requests.post(url, headers=headers, json=data, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Paystack error: {e}")
        return {"status": False, "message": str(e)}

def verify_paystack_payment(reference: str) -> dict:
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Verification error: {e}")
        return {"status": False, "message": str(e)}

# Job Search Utils
def get_jobs(query: str, filters: dict = None) -> list:
    filters = filters or {}
    url = "https://jsearch.p.rapidapi.com/search"
    headers = {
        "X-RapidAPI-Key": settings.RAPIDAPI_KEY,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
    }
    params = {"query": query, "num_pages": 1, "date_posted": "week"}
    params.update(filters)
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        return response.json().get("data", [])
    except Exception as e:
        logger.error(f"Job fetch error: {e}")
        return []

def get_jobs_arbeitnow(query: str, filters: dict = None) -> list:
    url = "https://www.arbeitnow.com/api/job-board-api"
    try:
        response = requests.get(url, timeout=15)
        jobs = response.json().get("data", [])
        query_lower = query.lower()
        # Basic keyword filter
        filtered = [
            job for job in jobs
            if query_lower in job.get("title", "").lower() or query_lower in job.get("company_name", "").lower()
        ]
        # Additional filters (e.g., remote, full-time)
        if filters:
            if filters.get("remote"):
                filtered = [job for job in filtered if job.get("remote", False)]
            if filters.get("job_employment_type"):
                filtered = [
                    job for job in filtered
                    if any(
                        filters["job_employment_type"].lower() in jt.lower()
                        for jt in job.get("job_types", [])
                    )
                ]
            if filters.get("job_experience_level"):
                # Arbeitnow does not provide experience level, so skip or implement if available
                pass
        # Normalize to match jsearch keys
        normalized = []
        for job in filtered:
            # Convert created_at (UNIX timestamp) to ISO date string
            created_at = job.get("created_at")
            if created_at:
                try:
                    job_posted_at = datetime.datetime.utcfromtimestamp(int(created_at)).isoformat()
                except Exception:
                    job_posted_at = str(created_at)
            else:
                job_posted_at = "N/A"
            normalized.append({
                "job_id": str(job.get("slug", job.get("id", "arbeitnow_" + job.get("title", "")))),
                "job_title": job.get("title", "N/A"),
                "employer_name": job.get("company_name", "Unknown"),
                "job_city": job.get("location", "N/A"),
                "job_country": job.get("location", "N/A"),  # Arbeitnow location is a string, not split
                "job_employment_type": ", ".join(job.get("job_types", [])),
                "job_posted_at": job_posted_at,
                "job_description": job.get("description", ""),
                "job_apply_link": job.get("url", None),
                "remote": job.get("remote", False),
            })
        return normalized
    except Exception as e:
        logger.error(f"Arbeitnow fetch error: {e}")
        return []
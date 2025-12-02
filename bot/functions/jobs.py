import requests
import logging
from django.conf import settings
import datetime

logger = logging.getLogger(__name__)



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

def get_jobs_remotive(query: str, filters: dict = None) -> list:
    url = "https://remotive.com/api/remote-jobs"
    try:
        response = requests.get(url, timeout=15)
        if not response.ok:
            return []
        
        data = response.json()
        jobs = data.get("jobs", [])
        
        # Filter locally since API doesn't support search params well
        query_lower = query.lower()
        filtered = [
            job for job in jobs
            if query_lower in job.get("title", "").lower() or 
               query_lower in job.get("company_name", "").lower() or
               any(query_lower in tag.lower() for tag in job.get("tags", []))
        ]
        
        normalized = []
        for job in filtered:
            # Remotive dates are ISO strings usually
            pub_date = job.get("publication_date", "N/A")
            
            normalized.append({
                "job_id": str(job.get("id", hash(job.get("url")))),
                "job_title": job.get("title", "N/A"),
                "employer_name": job.get("company_name", "Unknown"),
                "job_city": job.get("candidate_required_location", "Remote"),
                "job_country": "Remote",
                "job_employment_type": job.get("job_type", "Full-time"),
                "job_posted_at": pub_date,
                "job_description": job.get("description", ""),
                "job_apply_link": job.get("url", None),
                "remote": True,
            })
        return normalized
    except Exception as e:
        logger.error(f"Remotive fetch error: {e}")
        return []

def get_jobs_jobicy(query: str, filters: dict = None) -> list:
    # Jobicy API supports some filtering but local filtering is safer for specific keywords
    url = "https://jobicy.com/api/v2/remote-jobs"
    try:
        response = requests.get(url, timeout=15)
        if not response.ok:
            return []
            
        data = response.json()
        jobs = data.get("jobs", [])
        
        query_lower = query.lower()
        filtered = [
            job for job in jobs
            if query_lower in job.get("jobTitle", "").lower() or 
               query_lower in job.get("companyName", "").lower()
        ]
        
        normalized = []
        for job in filtered:
            normalized.append({
                "job_id": str(job.get("id", hash(job.get("url")))),
                "job_title": job.get("jobTitle", "N/A"),
                "employer_name": job.get("companyName", "Unknown"),
                "job_city": job.get("jobGeo", "Remote"),
                "job_country": "Remote",
                "job_employment_type": job.get("jobType", "Full-time"),
                "job_posted_at": job.get("pubDate", "N/A"),
                "job_description": job.get("jobDescription", ""),
                "job_apply_link": job.get("url", None),
                "remote": True,
            })
        return normalized
    except Exception as e:
        logger.error(f"Jobicy fetch error: {e}")
        return []

def get_all_jobs(query: str, filters: dict = None) -> list:
    jobs = []
    
    # 1. JSearch (RapidAPI)
    jobs.extend(get_jobs(query, filters))
    
    # 2. Arbeitnow
    jobs.extend(get_jobs_arbeitnow(query, filters))
    
    # 3. Remotive
    jobs.extend(get_jobs_remotive(query, filters))
    
    # 4. Jobicy
    jobs.extend(get_jobs_jobicy(query, filters))
    
    return jobs
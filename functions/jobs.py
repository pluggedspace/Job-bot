import requests
import logging
from django.conf import settings
import datetime

logger = logging.getLogger(__name__)



# Job Search Utils *
def get_jobs(query: str, filters: dict = None) -> list:
    filters = filters or {}
    url = "https://jsearch.p.rapidapi.com/search"
    headers = {
        "X-RapidAPI-Key": settings.RAPIDAPI_KEY,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
    }
    params = {"query": query, "num_pages": 1, "date_posted": "month"}
    params.update(filters)
    logger.info(f"Searching JSearch for: {query}")
    try:
        response = requests.get(url, headers=headers, params=params, timeout=7)
        data = response.json().get("data", [])
        logger.info(f"JSearch returned {len(data)} results")
        return data
    except Exception as e:
        logger.error(f"JSearch fetch error: {e}")
        return []

def get_jobs_arbeitnow(query: str, filters: dict = None) -> list:
    url = "https://www.arbeitnow.com/api/job-board-api"
    logger.info(f"Searching Arbeitnow for: {query}")
    try:
        response = requests.get(url, timeout=7)
        jobs = response.json().get("data", [])
        logger.info(f"Arbeitnow returned {len(jobs)} total jobs from API")
        if jobs:
            logger.info(f"Arbeitnow sample title: {jobs[0].get('title')}")
            
        query_words = query.lower().split()
        # Permissive word-based filter: match if all words are present in title, company, OR description
        filtered = []
        for job in jobs:
            search_text = (job.get("title", "") + " " + 
                          job.get("company_name", "") + " " + 
                          job.get("description", "")).lower()
            if all(word in search_text for word in query_words):
                filtered.append(job)
                
        logger.info(f"Arbeitnow filtered down to {len(filtered)} jobs for query '{query}'")
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
                "source": "Arbeitnow"
            })
        return normalized
    except Exception as e:
        logger.error(f"Arbeitnow fetch error: {e}")
        return []

def get_jobs_remotive(query: str, filters: dict = None) -> list:
    url = "https://remotive.com/api/remote-jobs"
    logger.info(f"Searching Remotive for: {query}")
    try:
        response = requests.get(url, timeout=7)
        if not response.ok:
            logger.warning(f"Remotive API returned status {response.status_code}")
            return []
        
        data = response.json()
        jobs = data.get("jobs", [])
        logger.info(f"Remotive returned {len(jobs)} total jobs from API")
        if jobs:
            logger.info(f"Remotive sample title: {jobs[0].get('title')}")
        
        query_words = query.lower().split()
        filtered = []
        for job in jobs:
            search_text = (job.get("title", "") + " " + 
                          job.get("company_name", "") + " " + 
                          job.get("description", "") + " " + 
                          " ".join(job.get("tags", []))).lower()
            if all(word in search_text for word in query_words):
                filtered.append(job)
                
        logger.info(f"Remotive found {len(filtered)} jobs for query '{query}'")
        
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
                "source": "Remotive"
            })
        return normalized
    except Exception as e:
        logger.error(f"Remotive fetch error: {e}")
        return []

def get_jobs_jobicy(query: str, filters: dict = None) -> list:
    # Jobicy API v2
    # GET https://jobicy.com/api/v2/remote-jobs
    # Params: count (1-100), geo, industry, tag
    url = "https://jobicy.com/api/v2/remote-jobs"
    
    # Default params
    params = {
        "count": 20, # Default to 20
        "tag": query, # Keyword search in tag
    }
    
    if filters:
        # Map filters
        if filters.get("count"):
            params["count"] = filters["count"]
            
        location = filters.get("location") or filters.get("geo")
        # User requested specific behavior:
        # "default remote to any location since it doesnt technically have remote, 
        # and also if no location is provided it should use any location"
        if location and location.lower() not in ["any", "remote", "anywhere"]:
            params["geo"] = location
        else:
            # If explicit "any" or "remote" or missing, do not send 'geo' or send appropriate value if API supports specific "any" keyword?
            # Docs say: "jobGeo: Geographic restriction... (or Anywhere if not applicable)"
            # Docs say default geo is "all regions". So omitting it is best for "any".
            pass 
            
        if filters.get("industry"):
            params["industry"] = filters["industry"]
            
    logger.info(f"Searching Jobicy for: {query} with params: {params}")
    try:
        response = requests.get(url, params=params, timeout=7)
        if not response.ok:
            logger.warning(f"Jobicy API returned status {response.status_code}")
            return []
            
        data = response.json()
        jobs = data.get("jobs", [])
        logger.info(f"Jobicy returned {len(jobs)} total jobs from API")
        
        normalized = []
        for job in jobs:
            # v2 Structure:
            # "id", "url", "jobTitle", "companyName", "companyLogo", "jobIndustry", "jobType", 
            # "jobGeo", "jobLevel", "jobExcerpt", "jobDescription", "pubDate", "salaryMin", ...
            
            geo = job.get("jobGeo", "Anywhere")
            
            normalized.append({
                "job_id": str(job.get("id", hash(job.get("url")))),
                "job_title": job.get("jobTitle", "N/A"),
                "employer_name": job.get("companyName", "Unknown"),
                "job_city": geo, 
                "job_country": geo, # Jobicy puts country/region in jobGeo usually
                "job_employment_type": ", ".join(job.get("jobType", ["Full-time"])),
                "job_posted_at": job.get("pubDate", "N/A"),
                "job_description": job.get("jobDescription", "") or job.get("jobExcerpt", ""),
                "job_apply_link": job.get("url", None),
                "remote": True, # Jobicy is all remote
                "source": "Jobicy"
            })
        return normalized
    except Exception as e:
        logger.error(f"Jobicy fetch error: {e}")
        return []

# New Integration: Adzuna *
def get_jobs_adzuna(query: str, filters: dict = None) -> list:
    app_id = settings.ADZUNA_APP_ID
    app_key = settings.ADZUNA_APP_KEY
    if not app_id or not app_key:
        logger.warning("Adzuna credentials missing")
        return []
        
    # Adzuna API endpoint structure: http://api.adzuna.com/v1/api/jobs/gb/search/1
    # We default to 'gb' (UK) or 'us' if not specified, but let's try 'us' for broad reach or from settings if we had a country setting
    country = filters.get('country', 'us') if filters else 'us'
    url = f"http://api.adzuna.com/v1/api/jobs/{country}/search/1"
    
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "what": query,
        "results_per_page": 10,
        "content-type": "application/json"
    }
    
    logger.info(f"Searching Adzuna ({country}) for: {query}")
    try:
        response = requests.get(url, params=params, timeout=7)
        if not response.ok:
            logger.warning(f"Adzuna API returned status {response.status_code}")
            return []
            
        data = response.json()
        results = data.get("results", [])
        logger.info(f"Adzuna returned {len(results)} jobs")
        
        normalized = []
        for job in results:
            normalized.append({
                "job_id": str(job.get("id", job.get("redirect_url"))),
                "job_title": job.get("title", "N/A"),
                "employer_name": job.get("company", {}).get("display_name", "Unknown"),
                "job_city": job.get("location", {}).get("display_name", "N/A"),
                "job_country": country.upper(),
                "job_employment_type": job.get("contract_type", "Full-time"), # Adzuna specific field
                "job_posted_at": job.get("created", "N/A"), # ISO format usually
                "job_description": job.get("description", ""),
                "job_apply_link": job.get("redirect_url", None),
                "remote": False, # Adzuna doesn't easily flag remote in top level
                "source": "Adzuna"
            })
        return normalized
    except Exception as e:
        logger.error(f"Adzuna fetch error: {e}")
        return []

# New Integration: Careerjet
def get_jobs_careerjet(query: str, filters: dict = None) -> list:
    # Use REST API directly as per docs
    api_key = settings.CAREERJET_API_KEY
    if not api_key:
        logger.warning("Careerjet API key missing")
        return []

    # Map country codes to Careerjet locales
    # Defaults to settings.CAREERJET_LOCALE or en_GB
    requested_country = filters.get('country', '').lower() if filters else ''
    
    # Simple mapping of common codes (expand as needed)
    locale_map = {
        'us': 'en_US', 'gb': 'en_GB', 'uk': 'en_GB', 'ca': 'en_CA', 
        'au': 'en_AU', 'nz': 'en_NZ', 'za': 'en_ZA', 'ie': 'en_IE',
        'fr': 'fr_FR', 'de': 'de_DE', 'nl': 'nl_NL', 'it': 'it_IT',
        'es': 'es_ES', 'pl': 'pl_PL', 'ru': 'ru_RU', 'ua': 'uk_UA',
        'se': 'sv_SE', 'no': 'no_NO', 'dk': 'da_DK', 'fi': 'fi_FI',
        'pt': 'pt_PT', 'br': 'pt_BR', 'mx': 'es_MX', 'ar': 'es_AR',
        'cl': 'es_CL', 'co': 'es_CO', 'pe': 'es_PE', 've': 'es_VE',
        'vn': 'vi_VN', 'my': 'ms_MY', 'ph': 'en_PH', 'sg': 'en_SG',
        'cn': 'zh_CN', 'jp': 'ja_JP', 'kr': 'ko_KR', 'tw': 'zh_TW',
        'in': 'en_IN', # India usually en_IN
    }
    
    # Determine locale:
    # 1. Explicit 'locale_code' filter
    # 2. Mapped 'country' filter
    # 3. Default from settings
    # 4. Fallback 'en_GB'
    
    locale = None
    if filters:
        locale = filters.get('locale_code')
    
    if not locale and requested_country:
        locale = locale_map.get(requested_country)
        
    if not locale:
        locale = settings.CAREERJET_LOCALE or 'en_GB'

    url = "https://search.api.careerjet.net/v4/query"
    
    # Construct Client IP and User Agent - required by API
    # In a real view, we'd pass request.META.get('REMOTE_ADDR') and 'HTTP_USER_AGENT'
    # Here strictly as a backend task, so we fake it or use server's info.
    # Docs: "user_ip string required", "user_agent string required"
    user_ip = filters.get('user_ip', '127.0.0.1') if filters else '127.0.0.1'
    user_agent = filters.get('user_agent', 'JobBot/1.0') if filters else 'JobBot/1.0'
    location = filters.get('location', '') if filters else ''

    params = {
        'locale_code': locale,
        'keywords': query,
        'location': location,
        'user_ip': user_ip,
        'user_agent': user_agent,
        'page_size': 20,
        'sort': 'relevance',
        # 'affid': '213e213hd12345' # Not listed in v4 'required' params in the snippet provided by user, 
                                    # but auth is via Basic Header.
    }
    
    # Basic Auth: API Key as username, password empty
    auth = (api_key, '')
    
    logger.info(f"Searching Careerjet ({locale}) for: {query}")
    try:
        response = requests.get(url, params=params, auth=auth, timeout=7)
        if not response.ok:
            logger.warning(f"Careerjet API returned status {response.status_code}")
            return []
            
        data = response.json()
        jobs = data.get("jobs", [])
        logger.info(f"Careerjet returned {len(jobs)} jobs")
        
        normalized = []
        for job in jobs:
            # V4 Job structure:
            # {'title': '...', 'company': '...', 'date': '...', 'description': '...', 'locations': '...', 'url': '...', ...}
            normalized.append({
                "job_id": job.get("url", hash(job.get("title"))),
                "job_title": job.get("title", "N/A"),
                "employer_name": job.get("company", "Unknown"),
                "job_city": job.get("locations", "N/A"),
                "job_country": locale.split('_')[-1] if '_' in locale else "N/A",
                "job_employment_type": "N/A", # Not provided in snippet details, usually contract_type in params, but not in job response? 
                                              # Actually snippet says 'contract_type' is a param, assume not in response unless we requested?
                                              # Docs say 'salary search' etc. 
                "job_posted_at": job.get("date", "N/A"),
                "job_description": job.get("description", ""),
                "job_apply_link": job.get("url", None),
                "remote": False, # Careerjet specific remote logic needs mapping if valid
                "source": "Careerjet"
            })
        return normalized
    except Exception as e:
        logger.error(f"Careerjet fetch error: {e}")
        return []

# New Integration: Findwork.dev
def get_jobs_findwork(query: str, filters: dict = None) -> list:
    token = settings.FINDWORK_API_KEY
    if not token:
        logger.warning("Findwork.dev API key missing")
        return []
        
    url = "https://findwork.dev/api/jobs/"
    headers = {"Authorization": f"Token {token}"}
    params = {"search": query, "sort_by": "relevance"}
    
    logger.info(f"Searching Findwork.dev for: {query}")
    try:
        response = requests.get(url, headers=headers, params=params, timeout=7)
        if not response.ok:
            logger.warning(f"Findwork API returned status {response.status_code}")
            return []
            
        data = response.json()
        results = data.get("results", [])
        logger.info(f"Findwork returned {len(results)} jobs")
        
        normalized = []
        for job in results:
            normalized.append({
                "job_id": str(job.get("id")),
                "job_title": job.get("role", "N/A"),
                "employer_name": job.get("company_name", "Unknown"),
                "job_city": job.get("location", "N/A"),
                "job_country": "N/A", # Sometimes in location text
                "job_employment_type": ", ".join(job.get("employment_type", []) or []) if job.get("employment_type") else "N/A",
                "job_posted_at": job.get("date_posted", "N/A"),
                "job_description": job.get("text", ""),
                "job_apply_link": job.get("url", None),
                "remote": job.get("remote", False),
                "source": "Findwork.dev"
            })
        return normalized
    except Exception as e:
        logger.error(f"Findwork fetch error: {e}")
        return []

# New Integration: Jooble *
def get_jobs_jooble(query: str, filters: dict = None) -> list:
    api_key = settings.JOOBLE_API_KEY
    if not api_key:
        logger.warning("Jooble API key missing")
        return []
        
    url = f"https://jooble.org/api/{api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {"keywords": query, "page": 1}
    
    logger.info(f"Searching Jooble for: {query}")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=7)
        if not response.ok:
            logger.warning(f"Jooble API returned status {response.status_code}")
            return []
            
        data = response.json()
        jobs = data.get("jobs", [])
        logger.info(f"Jooble returned {len(jobs)} jobs")
        
        normalized = []
        for job in jobs:
            normalized.append({
                "job_id": str(job.get("id", hash(job.get("link")))),
                "job_title": job.get("title", "N/A"),
                "employer_name": job.get("company", "Unknown"),
                "job_city": job.get("location", "N/A"),
                "job_country": "N/A",
                "job_employment_type": job.get("type", "N/A"),
                "job_posted_at": job.get("updated", "N/A"),
                "job_description": job.get("snippet", ""),
                "job_apply_link": job.get("link", None),
                "remote": False, # Not explicitly returned usually
                "source": "Jooble"
            })
        return normalized
    except Exception as e:
        logger.error(f"Jooble fetch error: {e}")
        return []

# New Integration: Authentic Jobs (RSS)
def get_jobs_authentic(query: str, filters: dict = None) -> list:
    # Uses feedparser
    try:
        import feedparser
    except ImportError:
        logger.error("feedparser not installed")
        return []
        
    # Official RSS feed: https://authenticjobs.com/feed/
    # We can't easily filter strictly by server-side query on RSS without fetching all
    # But usually RSS has query params, Authentic Jobs seems not to document search params for RSS well,
    # often it's just categories.
    # However, let's fetch the main feed and client-side filter.
    url = "https://authenticjobs.com/feed/"
    
    logger.info(f"Fetching Authentic Jobs RSS")
    try:
        feed = feedparser.parse(url)
        entries = feed.entries
        logger.info(f"Authentic Jobs RSS returned {len(entries)} entries")
        
        query_words = query.lower().split()
        filtered = []
        
        for entry in entries:
            # Basic client-side filtering
            search_text = (entry.title + " " + entry.description).lower()
            if all(word in search_text for word in query_words):
                filtered.append(entry)
                
        logger.info(f"Authentic Jobs matched {len(filtered)} entries locally")
        
        normalized = []
        for job in filtered:
            # RSS fields map loosely
            normalized.append({
                "job_id": job.get("id", job.link),
                "job_title": job.title,
                "employer_name": "Unknown", # Often in title "Company: Role" or summary
                "job_city": "Remote", # Authentic Jobs is heavy on creative/web/remote
                "job_country": "Remote",
                "job_employment_type": "Full-time", # Assumption
                "job_posted_at": job.get("published", "N/A"),
                "job_description": job.description,
                "job_apply_link": job.link,
                "remote": True, # Assumption for this feed usually
                "source": "Authentic Jobs"
            })
        return normalized
    except Exception as e:
        logger.error(f"Authentic Jobs fetch error: {e}")
        return []

def get_all_jobs(query: str, filters: dict = None) -> list:
    logger.info(f"Aggregating jobs for query: '{query}' with filters: {filters}")
    jobs = []
    
    # 1. JSearch (RapidAPI)
    jsearch_jobs = get_jobs(query, filters)
    for job in jsearch_jobs:
        job["source"] = "JSearch"
    jobs.extend(jsearch_jobs)
    
    # 2. Arbeitnow
    arbeitnow_jobs = get_jobs_arbeitnow(query, filters)
    jobs.extend(arbeitnow_jobs)
    
    # 3. Remotive
    remotive_jobs = get_jobs_remotive(query, filters)
    jobs.extend(remotive_jobs)
    
    # 4. Jobicy
    jobicy_jobs = get_jobs_jobicy(query, filters)
    jobs.extend(jobicy_jobs)
    
    # 5. Adzuna
    adzuna_jobs = get_jobs_adzuna(query, filters)
    jobs.extend(adzuna_jobs)
    
    # 6. Careerjet
    careerjet_jobs = get_jobs_careerjet(query, filters)
    jobs.extend(careerjet_jobs)
    
    # 7. Findwork.dev
    findwork_jobs = get_jobs_findwork(query, filters)
    jobs.extend(findwork_jobs)
    
    # 8. Jooble
    jooble_jobs = get_jobs_jooble(query, filters)
    jobs.extend(jooble_jobs)
    
    # 9. Authentic Jobs
    authentic_jobs = get_jobs_authentic(query, filters)
    jobs.extend(authentic_jobs)
    
    logger.info(f"Total jobs aggregated: {len(jobs)}")
    return jobs

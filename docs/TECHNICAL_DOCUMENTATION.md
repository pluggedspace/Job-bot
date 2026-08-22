# Job Bot - Technical Documentation

## Table of Contents
- [Architecture Overview](#architecture-overview)
- [Technology Stack](#technology-stack)
- [Database Schema](#database-schema)
- [REST API](#rest-api)
- [Authentication & Authorization](#authentication--authorization)
- [Telegram Bot](#telegram-bot)
- [WhatsApp Bot](#whatsapp-bot)
- [Job Search Aggregation](#job-search-aggregation)
- [Background Tasks (Celery)](#background-tasks-celery)
- [Feature Flags](#feature-flags)
- [Deployment Guide](#deployment-guide)
- [Development Setup](#development-setup)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

---

## Architecture Overview

Job Bot is a **self-hosted, single-user** job search and career preparation assistant. It is built as a Django application that exposes a REST API and runs Telegram/WhatsApp bots.

```
┌─────────────────────────────────────────────────────┐
│                    Django API                       │
│              (jobsearchbot project)                 │
│                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐  │
│  │  REST API    │  │  Telegram    │  │  WhatsApp │  │
│  │  (/api/)     │  │  Bot         │  │  Bot      │  │
│  └──────┬───────┘  └──────┬───────┘  └─────┬─────┘  │
│         │                 │                │        │
│  ┌──────▼─────────────────▼────────────────▼─────┐  │
│  │              PostgreSQL Database              │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
         │                        │
    ┌────▼────┐            ┌──────▼──────┐
    │  Redis  │            │  Celery     │
    │ (broker)│            │  Worker     │
    └─────────┘            │  + Beat     │
                           └─────────────┘
```

### Components

1. **Django API** — REST API with Django Rest Framework, protected by a static API token
2. **Telegram Bot** — Primary user interface, full-featured via `python manage.py run_bot`
3. **WhatsApp Bot** — Optional, via Meta WhatsApp Business API webhook
4. **PostgreSQL** — Primary data store
5. **Redis + Celery** — Background job alert checking and scheduled tasks
6. **External APIs** — Job search providers (JSearch, Adzuna, Careerjet, etc.) and AI providers (Groq, Gemini, Mistral)

### Key Design Decisions

- **Single-user mode**: No multi-tenancy, no external auth service. One default user via `User.get_default_user()` for API access.
- **Static API token**: `API_TOKEN` in `.env` → `Authorization: Bearer <token>` header.
- **Feature flags**: `ENABLE_PREMIUM=true` unlocks all features by default; `ENABLE_PAYMENTS=false` disables payment providers.
- **No web frontend**: `/` serves a simple self-hosted status page. The REST API is ready for custom frontends.

---

## Technology Stack

### Backend
- **Framework**: Django 5.x
- **API**: Django Rest Framework
- **Database**: PostgreSQL 15
- **ORM**: Django ORM
- **Async**: Python asyncio for bot handlers
- **Authentication**: Static API token (Bearer)
- **API Docs**: drf-spectacular (OpenAPI/Swagger/ReDoc)

### Bots
- **Telegram**: python-telegram-bot library (polling or webhook)
- **WhatsApp**: Meta WhatsApp Business API (direct HTTP webhook)

### Background Tasks
- **Celery**: Worker + Beat for scheduled job alert checks
- **Redis**: Message broker and result backend

### Infrastructure
- **Containerization**: Docker + docker-compose
- **Web Server**: Gunicorn (production)
- **Static Files**: WhiteNoise
- **Monitoring**: Sentry (optional)

### AI & Job Search
- **AI Providers**: Groq, Gemini, Mistral (for CV review, cover letters, interview practice, career paths)
- **Job Search**: JSearch (RapidAPI), Adzuna, Careerjet, Findwork, Jooble, Arbeitnow, Remotive, Jobicy, Authentic Jobs

---

## Database Schema

### Core Models

#### User
Single-user profile for Telegram, WhatsApp, and API access.

```python
class User(models.Model):
    user_id = models.CharField(max_length=100, unique=True)
    username = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    full_name = models.CharField(max_length=255, null=True, blank=True)

    telegram_id = models.CharField(max_length=100, null=True, blank=True, unique=True)
    whatsapp_id = models.CharField(max_length=100, null=True, blank=True, unique=True)
    platform_type = models.CharField(
        max_length=20,
        choices=[("telegram", "Telegram"), ("whatsapp", "WhatsApp"), ("api", "API")],
        default="telegram",
    )

    subscription_status = models.CharField(max_length=20, default="Free")
    payment_reference = models.CharField(max_length=100, null=True, blank=True)
    search_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    cv_data = models.JSONField(null=True, blank=True)
    current_job_title = models.CharField(max_length=255, null=True, blank=True)
    skills = models.JSONField(default=list, blank=True)
```

**`get_default_user()`**: Returns (or creates) the single default user for API access:

```python
@classmethod
def get_default_user(cls):
    user, _ = cls.objects.get_or_create(
        user_id="default",
        defaults={"username": "owner", "platform_type": "api"},
    )
    return user
```

#### Job
Jobs saved by the user.

```python
class Job(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="jobs")
    job_id = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    saved_at = models.DateTimeField(auto_now_add=True)
```

#### Alert
User-configured job search alerts.

```python
class Alert(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="alerts")
    query = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)
```

#### CareerPathCache
Cached career path results to avoid repeated AI calls.

```python
class CareerPathCache(models.Model):
    input_title = models.CharField(max_length=255, unique=True)
    normalized_title = models.SlugField(max_length=255, unique=True)
    result_data = models.JSONField()
    updated_at = models.DateTimeField(auto_now=True)
```

#### InterviewSession / InterviewResponse
Mock interview practice sessions.

```python
class InterviewSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    job_title = models.CharField(max_length=255)
    started_at = models.DateTimeField(auto_now_add=True)
    is_complete = models.BooleanField(default=False)
    current_question = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=5)

class InterviewResponse(models.Model):
    session = models.ForeignKey(InterviewSession, on_delete=models.CASCADE)
    question = models.TextField()
    answer = models.TextField()
    is_follow_up = models.BooleanField(default=False)
```

### Relationships

- **One-to-Many**: `User` → `Job`, `Alert`, `InterviewSession`
- **One-to-Many**: `InterviewSession` → `InterviewResponse`

---

## REST API

All endpoints are under `/api/` and require `Authorization: Bearer <API_TOKEN>`.

### Interactive Documentation

OpenAPI/Swagger docs are auto-generated with **drf-spectacular**:

| URL | Description |
|-----|-------------|
| `/api/schema/` | OpenAPI schema (JSON) |
| `/api/docs/` | Swagger UI |
| `/api/redoc/` | ReDoc UI |

### User Profile

```
GET   /api/user/profile/    Get current user profile
PATCH /api/user/profile/    Update user profile (partial)
```

### Job Search

```
POST  /api/jobs/search/     Search for jobs
      Body: {"query": "python developer", "filters": {...}}

GET   /api/jobs/saved/      Get saved jobs
POST  /api/jobs/saved/      Save a job
```

### Alerts

```
GET    /api/alerts/         List alerts
POST   /api/alerts/         Create alert
GET    /api/alerts/{id}/    Get alert
PUT    /api/alerts/{id}/    Update alert
PATCH  /api/alerts/{id}/    Partial update
DELETE /api/alerts/{id}/    Delete alert
POST   /api/alerts/{id}/toggle/   Toggle alert active state
```

### Career Tools

```
POST  /api/career/path/     Get career path for a role
      Body: {"role": "software engineer"}

POST  /api/career/upskill/  Get upskill plan
      Body: {"current_role": "...", "target_role": "..."}
```

### Interview Practice

```
POST   /api/interview/practice/   Start or respond to interview
       Body: {"message": "user response"} or {} to start

GET    /api/interview/session/    Check active session
DELETE /api/interview/session/    Cancel/end session
```

### CV Tools

```
POST  /api/cv/review/       Get AI CV review
POST  /api/cv/coverletter/  Generate cover letter
      Body: {"job_title": "Software Engineer", "company": "Google"}
```

### Subscription / Quota

```
POST  /api/subscription/create/   Create subscription (disabled unless ENABLE_PAYMENTS=true)
POST  /api/subscription/verify/   Verify payment (disabled unless ENABLE_PAYMENTS=true)
GET   /api/subscription/quota/    Get quota and subscription status
```

### Webhooks

```
POST  /api/whatsapp/webhook/   WhatsApp webhook (Meta)
GET   /api/whatsapp/webhook/   WhatsApp webhook verification
```

### Other Endpoints

```
GET   /health/          Health check
GET   /                Status page (self-hosted)
GET   /robots.txt      Robots file
POST  /webhook/        Telegram webhook (if using webhook mode)
```

---

## Authentication & Authorization

### API Authentication

The REST API uses a **static API token** from the environment:

1. Set `API_TOKEN` in `.env`
2. Include `Authorization: Bearer <API_TOKEN>` in every request
3. The `APITokenAuthentication` class validates the token and returns the default user

```python
# bot/authentication.py
class APITokenAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        api_token = getattr(settings, "API_TOKEN", None)
        if not api_token:
            return None

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split("Bearer ", 1)[1].strip()
        if token != api_token:
            raise exceptions.AuthenticationFailed("Invalid API token")

        bot_user = User.get_default_user()
        return (APITokenUser(bot_user), None)
```

### Bot Authentication

Bots use platform IDs (Telegram ID, WhatsApp phone number) for identification. No API token required for bot requests.

### Session Authentication

Django session authentication is also enabled for the Django admin (`/admin/`).

---

## Telegram Bot

The Telegram bot is the **primary user interface**. It runs via:

```bash
python manage.py run_bot
```

### Commands

| Command | Description |
|---------|-------------|
| `/start` | Initialize bot and show welcome message |
| `/findjobs <query>` | Search for jobs (e.g., `/findjobs python remote`) |
| `/history` | View saved jobs |
| `/build_cv` | Create a professional CV |
| `/view_cv` | View current CV |
| `/cv_review` | Get AI feedback on CV |
| `/coverletter <Job> \| <Company>` | Generate a cover letter |
| `/setalert <keyword>` | Create a job alert |
| `/myalerts` | Manage alerts |
| `/careerpath <role>` | Explore career progression |
| `/upskill <role>` | Get a personalized learning plan |
| `/practice` | Start a mock interview |
| `/subscribe <email>` | Upgrade to premium (if payments enabled) |
| `/quota` | Check free search limit |

### Implementation

- **File**: `bot/bot.py` — `JobSearchBot` class
- **Library**: python-telegram-bot with `AIORateLimiter`
- **Mode**: Polling by default (`run_polling()`); webhook mode available via `POST /webhook/`

### Webhook Mode

To use webhook mode instead of polling:

```bash
python manage.py set_telegram_webhook
```

Then configure your reverse proxy to forward `POST /webhook/` to the Django app.

---

## WhatsApp Bot

The WhatsApp bot is **optional** and uses the Meta WhatsApp Business API.

### Setup

1. Create a Meta Developer account
2. Create a WhatsApp Business App
3. Configure environment variables:
   - `META_ACCESS_TOKEN`
   - `META_PHONE_NUMBER_ID`
   - `META_VERIFY_TOKEN`
4. Set webhook URL: `https://yourdomain.com/api/whatsapp/webhook/`

### Message Handling

Same commands as Telegram, text-based. See `docs/WHATSAPP_SETUP.md` for full setup instructions.

### Implementation

- **File**: `bot/whatsapp_bot.py` — `whatsapp_bot` instance
- **Webhook**: `bot/api/whatsapp_webhook.py` — `WhatsAppWebhookView`

---

## Job Search Aggregation

Job search aggregates results from multiple providers in `bot/functions/jobs.py`:

| Provider | Type | Requires |
|----------|------|----------|
| JSearch (RapidAPI) | REST API | `RAPIDAPI_KEY` |
| Adzuna | REST API | `ADZUNA_APP_ID`, `ADZUNA_APP_KEY` |
| Careerjet | REST API | `CAREERJET_API_KEY` |
| Findwork.dev | REST API | `FINDWORK_API_KEY` |
| Jooble | REST API | `JOOBLE_API_KEY` |
| Arbeitnow | REST API | None |
| Remotive | REST API | None |
| Jobicy | REST API | None |
| Authentic Jobs | RSS Feed | None |

Results are normalized to a common schema and filtered to jobs posted within the last 2 days.

---

## Background Tasks (Celery)

Celery handles scheduled job alert checks.

### Tasks

- **`bot.tasks.check_alerts`** — Runs every 30 minutes (via Celery Beat), checks all active alerts, and sends Telegram notifications for new matching jobs.

### Services

- **`bot/services/career_path.py`** — Career path resolution with caching
- **`bot/services/upskill.py`** — Upskill plan generation
- **`bot/services/interview.py`** — Mock interview session management
- **`bot/services/user_context.py`** — User context helpers

---

## Feature Flags

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_PREMIUM` | `true` | Unlocks all premium features (CV review, cover letters, interview practice, unlimited searches) |
| `ENABLE_PAYMENTS` | `false` | Enables Paystack/Flutterwave payment integration |

When `ENABLE_PREMIUM=true`, all users are treated as premium regardless of `subscription_status`.

When `ENABLE_PAYMENTS=false`, subscription endpoints return `501 Not Implemented`.

---

## Deployment Guide

### Environment Variables

Create `.env` file (see `.env.example`):

```bash
# Django
DJANGO_SECRET_KEY=change-me-in-production
DEBUG=false
ALLOWED_HOSTS=yourdomain.com

# Database (PostgreSQL)
POSTGRES_DB=jobbot
POSTGRES_USER=jobbot
POSTGRES_PASSWORD=your-db-password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Single-user API access
API_TOKEN=generate-a-long-random-token

# Feature flags (self-hosted defaults)
ENABLE_PREMIUM=true
ENABLE_PAYMENTS=false

# Telegram bot (primary UI)
TELEGRAM_BOT_TOKEN=your-telegram-token

# Celery / Redis
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Job search APIs (at least one recommended)
ADZUNA_APP_ID=
ADZUNA_APP_KEY=
CAREERJET_API_KEY=
FINDWORK_API_KEY=
JOOBLE_API_KEY=
RAPIDAPI_KEY=

# AI providers (for CV review, cover letters, interview practice)
GROQ_API_KEY=
GEMINI_API_KEY=
MISTRAL_API_KEY=

# Optional: WhatsApp
META_ACCESS_TOKEN=
META_PHONE_NUMBER_ID=
META_VERIFY_TOKEN=

# Optional: Monitoring
SENTRY_DSN=
```

### Docker Deployment

```bash
# Build and run all services
docker compose up -d

# Run migrations
docker compose exec job-web python manage.py migrate

# Create superuser (for admin)
docker compose exec job-web python manage.py createsuperuser
```

Services: `job-web` (Gunicorn API), `job-bot` (Telegram bot), `db` (PostgreSQL), `redis`, `celery` (worker), `celery-beat`.

### Local Deployment

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your tokens and keys

# Run migrations
python manage.py migrate

# Start API server
python manage.py runserver

# In another terminal, start the Telegram bot
python manage.py run_bot

# In another terminal, start Celery worker + beat
celery -A jobsearchbot worker --loglevel=info
celery -A jobsearchbot beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### Production Checklist

- [ ] Set `DEBUG=false`
- [ ] Configure proper `ALLOWED_HOSTS`
- [ ] Set a strong `DJANGO_SECRET_KEY`
- [ ] Generate a strong `API_TOKEN`
- [ ] Use production database (PostgreSQL)
- [ ] Set up SSL/TLS certificates
- [ ] Configure webhook URLs for bots (or use polling)
- [ ] Set up monitoring and logging (Sentry optional)
- [ ] Configure backup strategy

---

## Development Setup

### Prerequisites
- Python 3.10+
- PostgreSQL 14+
- Redis
- Docker (optional)

### Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env

# Run migrations
python manage.py migrate

# Start development server
python manage.py runserver
```

### Bot Setup

```bash
# Start Telegram bot (polling mode)
python manage.py run_bot
```

### Management Commands

| Command | Description |
|---------|-------------|
| `python manage.py run_bot` | Run the Telegram bot (polling) |
| `python manage.py set_telegram_webhook` | Set the Telegram webhook URL |
| `python manage.py setup_tasks` | Set up Celery beat tasks |
| `python manage.py verify_changes` | Verify database changes |

---

## Testing

### Run Tests

```bash
# Backend tests
python manage.py test
```

### Manual Testing

Use tools like Postman, curl, or the Swagger UI at `/api/docs/` to test API endpoints. For bots, use the actual Telegram/WhatsApp apps.

Example curl:

```bash
curl -H "Authorization: Bearer YOUR_API_TOKEN" \
  http://127.0.0.1:8000/api/user/profile/
```

---

## Troubleshooting

### Common Issues

**Database Connection Error**:
- Check `POSTGRES_*` variables in `.env`
- Ensure PostgreSQL is running
- Verify credentials

**Bot Not Responding**:
- Check `TELEGRAM_BOT_TOKEN` in `.env`
- Verify the bot is running (`python manage.py run_bot`)
- Check server logs

**API Authentication Errors**:
- Verify `API_TOKEN` is set in `.env`
- Ensure `Authorization: Bearer <token>` header is correct
- Check that `API_TOKEN` matches exactly

**Job Search Returns No Results**:
- Verify at least one job search API key is configured
- Check API rate limits
- Try a broader search query

---

## Additional Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Django Rest Framework](https://www.django-rest-framework.org/)
- [drf-spectacular (OpenAPI)](https://drf-spectacular.readthedocs.io/)
- [python-telegram-bot](https://python-telegram-bot.org/)
- [WhatsApp Business API](https://developers.facebook.com/docs/whatsapp)
- [Celery](https://docs.celeryq.dev/)
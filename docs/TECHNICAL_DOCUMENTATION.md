# Job Bot - Technical Documentation

## Table of Contents
- [Architecture Overview](#architecture-overview)
- [Technology Stack](#technology-stack)
- [Database Schema](#database-schema)
- [Internal API Endpoints](#internal-api-endpoints)
- [Bot Integration](#bot-integration)
- [Authentication & Authorization](#authentication--authorization)
- [Deployment Guide](#deployment-guide)

---

## Architecture Overview

Job Bot is a multi-platform job search assistant built with a microservices architecture:

```
┌─────────────────┐
│   Next.js Web   │
│   Application   │
└────────┬────────┘
         │
         ├─────────────────┐
         │                 │
    ┌────▼────┐      ┌────▼────┐
    │  Kong   │      │ Django  │
    │ Gateway │◄─────┤   API   │
    └────┬────┘      └────┬────┘
         │                │
         │           ┌────▼────────┐
         │           │ PostgreSQL  │
         │           │  Database   │
         │           └─────────────┘
         │
    ┌────▼──────────────────┐
    │   Telegram Bot API    │
    │  WhatsApp Business    │
    └───────────────────────┘
```

### Components

1. **Frontend (Next.js)**: React-based web application with TypeScript
2. **Backend (Django)**: REST API with Django Rest Framework
3. **API Gateway (Kong)**: Request routing, authentication, and rate limiting
4. **Database (PostgreSQL)**: Primary data store
5. **Bot Services**: Telegram and WhatsApp bot handlers
6. **External APIs**: RapidAPI (job search), Gemini AI, Paystack (payments)

---

## Technology Stack

### Backend
- **Framework**: Django 4.x
- **API**: Django Rest Framework
- **Database**: PostgreSQL
- **ORM**: Django ORM
- **Async**: Python asyncio for bot handlers
- **Authentication**: JWT tokens (djangorestframework-simplejwt)

### Frontend
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **HTTP Client**: Axios
- **State Management**: React hooks

### Bots
- **Telegram**: python-telegram-bot library
- **WhatsApp**: Meta WhatsApp Business API (direct HTTP)

### Infrastructure
- **API Gateway**: Kong
- **Payments**: Paystack
- **AI Services**: Google Gemini API
- **Job Search**: RapidAPI (JSearch)

---

## Database Schema

### Core Models

#### TenantUser
Primary user model for web authentication.

```python
class TenantUser(models.Model):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    tenant = models.ForeignKey(Tenant)
    subscription_status = models.CharField()  # 'Free', 'Paid'
    search_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
```

#### User (Platform User)
Bot user model for Telegram/WhatsApp.

```python
class User(models.Model):
    telegram_id = models.BigIntegerField(unique=True, null=True)
    whatsapp_id = models.CharField(unique=True, null=True)
    username = models.CharField(max_length=100)
    platform_type = models.CharField()  # 'telegram', 'whatsapp'
    tenant_user = models.ForeignKey(TenantUser, null=True)
    subscription_status = models.CharField()
    search_count = models.IntegerField(default=0)
```

#### JobAlert
User-configured job search alerts.

```python
class JobAlert(models.Model):
    user = models.ForeignKey(User)
    query = models.CharField(max_length=500)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

#### SavedJob
Jobs saved by users.

```python
class SavedJob(models.Model):
    user = models.ForeignKey(User)
    job_id = models.CharField(max_length=255)
    title = models.CharField(max_length=500)
    company = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
```

#### LinkingCode
Temporary codes for account linking.

```python
class LinkingCode(models.Model):
    code = models.CharField(max_length=6, unique=True)
    platform_user = models.ForeignKey(User)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
```

### Relationships

- **One-to-One**: `User.tenant_user` → `TenantUser` (optional, for linked accounts)
- **One-to-Many**: `User` → `JobAlert`, `SavedJob`, `InterviewSession`
- **Many-to-One**: `TenantUser` → `Tenant`

---

## Internal API Endpoints

### Authentication

```
POST /api/auth/register/
POST /api/auth/login/
POST /api/auth/refresh/
GET  /api/auth/me/
```

### Job Search

```
GET  /api/jobs/search/?query={query}
POST /api/jobs/saved/
GET  /api/jobs/saved/
DELETE /api/jobs/saved/{id}/
```

### Alerts

```
GET  /api/alerts/
POST /api/alerts/
PUT  /api/alerts/{id}/toggle/
DELETE /api/alerts/{id}/
```

### User Profile

```
GET  /api/users/profile/
PUT  /api/users/profile/
GET  /api/users/quota/
```

### Premium Features

```
POST /api/premium/cv-review/
POST /api/premium/cover-letter/
POST /api/premium/career-path/
POST /api/premium/upskill-plan/
GET  /api/premium/interview/session/
POST /api/premium/interview/start/
POST /api/premium/interview/respond/
POST /api/premium/interview/stop/
```

### Account Linking

```
POST /api/link/account/
POST /api/link/unlink/
GET  /api/link/accounts/
```

### Subscription

```
POST /api/subscription/create/
POST /api/subscription/verify/
```

### Bot Webhooks

```
POST /api/telegram/webhook/
POST /api/whatsapp/webhook/
GET  /api/whatsapp/webhook/  # Verification
```

---

## Bot Integration

### Telegram Bot

**Setup**:
1. Create bot via @BotFather
2. Set `TELEGRAM_BOT_TOKEN` in environment
3. Configure webhook: `https://yourdomain.com/api/telegram/webhook/`

**Commands**:
- `/start` - Initialize bot
- `/search <query>` - Search for jobs
- `/alerts` - Manage job alerts
- `/link` - Generate linking code
- `/profile` - View profile
- `/subscribe` - Manage subscription

**Implementation**: `bot/bot.py`

### WhatsApp Bot

**Setup**:
1. Create Meta Developer account
2. Create WhatsApp Business App
3. Configure environment variables:
   - `META_ACCESS_TOKEN`
   - `META_PHONE_NUMBER_ID`
   - `META_VERIFY_TOKEN`
4. Set webhook: `https://yourdomain.com/api/whatsapp/webhook/`

**Message Handling**: Same commands as Telegram, text-based

**Implementation**: `bot/whatsapp_bot.py`

### Account Linking Flow

1. User types `/link` in bot
2. System generates 6-character code (valid 10 minutes)
3. User enters code on web app
4. System links `User` (bot) to `TenantUser` (web)
5. Shared quota, alerts, and subscription status

---

## Authentication & Authorization

### Web Authentication

**Flow**:
1. User registers/logs in via web
2. Backend generates JWT access + refresh tokens
3. Frontend stores tokens in localStorage
4. Requests include `Authorization: Bearer <token>` header
5. Kong gateway validates tokens

**Token Expiry**:
- Access token: 60 minutes
- Refresh token: 7 days

### Bot Authentication

Bots use platform IDs (Telegram ID, WhatsApp phone number) for identification. No JWT tokens required for bot requests.

### Multi-Tenancy

Each user belongs to a `Tenant` (organization). Data is isolated by tenant. Subscription status is per-tenant-user.

---

## Deployment Guide

### Environment Variables

Create `.env` file:

```bash
# Django
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/jobbot

# APIs
RAPIDAPI_KEY=your-rapidapi-key
GEMINI_API_KEY=your-gemini-key
PAYSTACK_SECRET_KEY=your-paystack-key

# Bots
TELEGRAM_BOT_TOKEN=your-telegram-token
META_ACCESS_TOKEN=your-whatsapp-token
META_PHONE_NUMBER_ID=your-phone-id
META_VERIFY_TOKEN=your-verify-token

# Kong
KONG_ADMIN_URL=http://kong:8001
```

### Docker Deployment

```bash
# Build and run
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser
```

### Production Checklist

- [ ] Set `DEBUG=False`
- [ ] Configure proper `ALLOWED_HOSTS`
- [ ] Use production database (PostgreSQL)
- [ ] Set up SSL/TLS certificates
- [ ] Configure Kong gateway
- [ ] Set webhook URLs for bots
- [ ] Configure payment gateway (Paystack)
- [ ] Set up monitoring and logging
- [ ] Configure backup strategy
- [ ] Set up CDN for static files

### Database Migrations

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Rollback migration
python manage.py migrate app_name previous_migration_name
```

---

## Development Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- Docker (optional)

### Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start development server
python manage.py runserver
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Bot Setup

Set webhook URLs in development:
```bash
# Telegram
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://yourdomain.com/api/telegram/webhook/"

# WhatsApp
# Configure in Meta Developer Console
```

---

## Testing

### Run Tests

```bash
# Backend tests
python manage.py test

# Frontend tests
cd frontend && npm test
```

### Manual Testing

Use tools like Postman or curl to test API endpoints. For bots, use the actual Telegram/WhatsApp apps.

---

## Troubleshooting

### Common Issues

**Database Connection Error**:
- Check `DATABASE_URL` in `.env`
- Ensure PostgreSQL is running
- Verify credentials

**Bot Not Responding**:
- Check webhook configuration
- Verify bot token
- Check server logs

**Authentication Errors**:
- Verify JWT token is valid
- Check token expiry
- Ensure Kong is configured correctly

---

## Additional Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [WhatsApp Business API](https://developers.facebook.com/docs/whatsapp)
- [Kong Gateway](https://docs.konghq.com/)

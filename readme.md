# Job Autobot (Job Bot)

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/django-5.x-green.svg)](https://www.djangoproject.com/)
[![Telegram](https://img.shields.io/badge/telegram-supported-blue.svg)](https://telegram.org/)
[![WhatsApp](https://img.shields.io/badge/whatsapp-optional-green.svg)](https://www.whatsapp.com/)

**Job Autobot** is a self-hosted, AI-powered job search and career preparation assistant. Deploy it on your own infrastructure and interact via **Telegram**, optional **WhatsApp**, or the **REST API**.

## Features

- Smart job aggregation from multiple sources
- CV builder, AI review, and cover letter generation
- Job alerts (Celery + Redis)
- Interview practice and career path tools
- Single-user mode — no multi-tenancy or external auth service required

## UI options

| Channel | Status | How |
|---------|--------|-----|
| **Telegram** | Primary, full-featured | `python manage.py run_bot` |
| **WhatsApp** | Optional | Meta Business API webhook — see `docs/WHATSAPP_SETUP.md` |
| **REST API** | Ready | Bearer token auth — build your own frontend or use curl |
| **Web UI** | Not included | API is ready; see [Frontend](#frontend) below |

There is **no web frontend in this repo**. The landing page at `/` is an internal status page for self-hosted deployments.

## Quick start

### Local

```bash
git clone https://github.com/pluggedspace/Job-bot.git
cd Job-bot
pip install -r requirements.txt
cp .env.example .env   # edit with your tokens and keys
python manage.py migrate
python manage.py runserver
```

In another terminal, start the Telegram bot:

```bash
python manage.py run_bot
```

Visit `http://127.0.0.1:8000/` for the status page. API calls use:

```bash
curl -H "Authorization: Bearer YOUR_API_TOKEN" http://127.0.0.1:8000/api/user/profile/
```

### Docker

```bash
cp .env.example .env
docker compose up -d
```

Services: web API, Telegram bot, PostgreSQL, Redis, Celery worker, Celery beat.

## Frontend

The REST API under `/api/` is complete for profile, jobs, alerts, career tools, CV, and interview features. Options for a web UI:

1. **Telegram-only** — simplest; no frontend needed
2. **Build a frontend** — any SPA (React, Vue, Svelte) against `/api/` with `Authorization: Bearer <API_TOKEN>`
3. **Open-source the frontend separately** — publish a `job-bot-web` repo when ready
4. **API clients** — Postman, Bruno, or scripts for automation

We recommend documenting your API token in `.env` and keeping `ENABLE_PREMIUM=true` for self-hosted use.

## Configuration

| Variable | Purpose |
|----------|---------|
| `API_TOKEN` | Secret token for REST API access |
| `TELEGRAM_BOT_TOKEN` | Telegram BotFather token |
| `ENABLE_PREMIUM` | `true` unlocks all features locally (default) |
| `ENABLE_PAYMENTS` | `false` disables Paystack/Flutterwave (default) |

See `.env.example` for the full list.

## Documentation

- [Technical documentation](docs/TECHNICAL_DOCUMENTATION.md)
- [User guide (Telegram/WhatsApp commands)](docs/USER_GUIDE.md)
- [WhatsApp setup](docs/WHATSAPP_SETUP.md)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE).

## Disclaimer

Job Autobot aggregates publicly available job listings. Verify listings independently before applying.

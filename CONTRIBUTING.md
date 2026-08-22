# Contributing to Job Bot

Thank you for your interest in contributing!

## Getting started

1. Fork the repository
2. Copy `.env.example` to `.env` and configure at minimum `API_TOKEN` and `TELEGRAM_BOT_TOKEN`
3. Run migrations: `python manage.py migrate`
4. Start the API: `python manage.py runserver`
5. Start the bot: `python manage.py run_bot`

## Pull requests

- Keep changes focused and minimal
- Match existing code style
- Update docs when changing behavior or configuration
- Test Telegram commands and API endpoints you touch

## Reporting issues

Include your Python version, database type, and relevant logs. Redact secrets and tokens.

## Scope

This project targets **single-user self-hosted** deployments. Please avoid reintroducing multi-tenancy or SaaS-specific coupling unless discussed in an issue first.

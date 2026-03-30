# Job Autobot (Job Bot) 🚀

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)  
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)  
[![Django 4.x](https://img.shields.io/badge/django-4.x-green.svg)](https://www.djangoproject.com/)  
[![Telegram](https://img.shields.io/badge/telegram-supported-blue.svg)](https://telegram.org/)  
[![WhatsApp](https://img.shields.io/badge/whatsapp-supported-green.svg)](https://www.whatsapp.com/)  

**Job Autobot** is an **AI-powered job search and preparation assistant** built with **Python Django** by **Pluggedspace Labs**.  

It aggregates jobs, helps build and optimize CVs, generates tailored cover letters, provides interview prep, and supports cross-platform usage on **Web, Telegram, and WhatsApp**.  

This project is now **open source**. Commercial use **requires attribution**:  

> Powered by Pluggedspace Labs  

---

## Features ✨

- **Smart Job Aggregation**: Pulls listings from LinkedIn, Indeed, Glassdoor, company pages, and freelance platforms using NLP.  
- **CV Builder & Optimization**: Guided resume creation, AI-powered reviews, and ATS optimization.  
- **Intelligent Job Alerts**: Receive notifications via Telegram, WhatsApp, or web.  
- **Application Assistance**: Tailored cover letters and job tracking.  
- **Interview Preparation**: Mock interviews covering behavioral and technical questions.  
- **Career Development Tools**: Career path visualization, skill gap analysis, and upskilling guidance.  

---

## Architecture Overview 🏗️

```text
      +----------------+
      |   Web / Mobile |
      +-------+--------+
              |
              v
      +----------------+
      |   Django API   |
      |  (REST / GraphQL)|
      +-------+--------+
              |
  +-----------+-----------+
  |                       |
  v                       v
Job Aggregator         AI Engine
(NLP + Crawlers)     (CV review, Alerts)
  |
  v
Messaging Platforms
(Telegram / WhatsApp)


---

Open Source Repository 📂

GitHub: https://github.com/pluggedspace/Job-bot

You can:

Fork and run locally

Customize job pipelines

Extend features or integrations

Experiment with Django + AI workflows



---

Quick Start 🏃‍♂️

Local Setup

git clone https://github.com/pluggedspace/Job-bot.git
cd Job-bot

# install dependencies
pip install -r requirements.txt

# copy env variables
cp .env.example .env

# apply migrations
python manage.py migrate

# run server
python manage.py runserver

Access the app at http://127.0.0.1:8000


---

Docker (Optional)

docker build -t job-autobot .
docker run -p 8000:8000 --env-file .env job-autobot


---

Contribution 🤝

We welcome contributions:

New job source integrations

NLP search improvements

UI/UX enhancements

ATS optimization logic

Messaging platform features

Performance tuning



---

License 📄

MIT License. Commercial deployments must include attribution:

> Powered by Pluggedspace Labs




---

Disclaimer ⚠️

Job Autobot aggregates publicly available job data. Users are responsible for verifying listings independently.


---

About Pluggedspace Labs 🧪

Focused on intelligent systems, automation, and human-AI collaboration, Pluggedspace Labs uses prototypes like Job Autobot to research workflows, orchestration, and automation. Insights from this project feed into Akili Weave (Atlas) — our primary AI engine.


---

Get Started 🚀

1. Fork the repo


2. Run locally or via Docker


3. Experiment, contribute, and improve the job search experience!




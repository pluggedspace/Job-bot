# Job Bot - User Guide

Welcome to Job Bot! Your AI-powered job search assistant available on Telegram, WhatsApp, and via REST API.

**Version**: 3.0  
**Last Updated**: August 2026

## Table of Contents
- [Overview](#overview)
- [Getting Started](#getting-started)
- [Commands Reference](#commands-reference)
- [Features](#features)
- [Using the Bots](#using-the-bots)
- [REST API](#rest-api)
- [Feature Flags](#feature-flags)
- [FAQ](#faq)
- [Support](#support)

---

## Overview

Job Bot leverages AI to streamline the job search process by providing:

- **Smart Job Search**: Find relevant opportunities using natural language queries
- **CV Building**: Create and optimize professional resumes
- **Career Guidance**: Get personalized career path recommendations
- **Application Tools**: Generate cover letters and improve your CV
- **Job Alerts**: Receive notifications for new matching positions
- **Interview Practice**: Prepare for interviews with AI-powered mock sessions

**Target Audience**: Self-hosted users who want a personal AI-powered job search assistant.

---

## Getting Started

### Telegram Bot (Primary)

1. Open Telegram
2. Search for your bot (created via @BotFather)
3. Click "Start" or type `/start`
4. The bot will create your account automatically
5. Start searching for jobs!

### WhatsApp Bot (Optional)

1. Open WhatsApp
2. Send a message to the Job Bot number
3. Type "Hi" or "Start"
4. The bot will create your account automatically
5. Start searching for jobs!

### REST API

The REST API is available for scripts, automation, or custom frontends. Authenticate with:

```bash
curl -H "Authorization: Bearer YOUR_API_TOKEN" \
  http://127.0.0.1:8000/api/user/profile/
```

---

## Commands Reference

### 🎯 Core Job Search Commands

#### `/findjobs [keywords] [location] [type]`
Searches for jobs across multiple platforms.

**Parameters:**
- `keywords` (required): Job title, skills, or company names
- `location` (optional): City, country, or "remote"
- `type` (optional): full-time, part-time, contract, internship

**Examples:**
```
/findjobs python developer
/findjobs data scientist london
/findjobs frontend developer remote full-time
/findjobs marketing manager new york
```

#### `/quota`
Shows your remaining job searches.

- **Free Users:** 25 searches
- **Premium Users (ENABLE_PREMIUM=true):** Unlimited searches

#### `/history`
Displays your saved jobs and search history.

---

### 📝 CV & Profile Management

#### `/build_cv`
Starts an interactive CV creation wizard with the following sections:
- Personal information
- Work experience (multiple positions)
- Education history
- Skills and competencies
- Projects and portfolio
- Certifications and awards
- References

The bot guides you through each section step by step.

#### `/view_cv`
Displays your current CV in a formatted, readable layout.

#### `/cv_review`
Provides AI-powered analysis of your CV with suggestions for:
- Formatting improvements
- Content optimization
- Keyword enhancement for ATS systems
- Section organization

**Premium Feature** — unlocked by default with `ENABLE_PREMIUM=true`.

---

### 🔔 Job Alerts System

#### `/setalert`
Creates personalized job alerts based on your criteria:
- Job titles and keywords
- Locations (or remote)
- Salary ranges
- Experience levels
- Company types

**Examples of alert criteria:**
- "Senior software engineer positions in Berlin"
- "Remote marketing jobs paying $80k+"
- "Entry-level data analyst roles"

#### `/myalerts`
Manages your active job alerts:
- View all active alerts
- Toggle alerts on/off
- Delete alerts

---

### 🚀 Career Development

#### `/careerpath [current_role]`
Explores career progression options and potential growth paths.

**Examples:**
```
/careerpath software developer
/careerpath marketing coordinator
/careerpath data analyst
```

**Provides:**
- Next-level positions (broader roles)
- Specialized positions (narrower roles)
- Alternative career paths (related roles)
- Required skills and experience

#### `/practice`
Interactive interview preparation with:
- Common behavioral questions
- Technical questions by field
- STAR method guidance
- Sample answers and feedback

**Premium Feature** — unlocked by default with `ENABLE_PREMIUM=true`.

#### `/upskill`
Generates personalized learning recommendations:
- Skill gaps analysis
- Online course suggestions with links
- Reading materials
- Project ideas
- Certification paths

---

### ✍️ Application Tools

#### `/coverletter Job Title | Company`
Generates tailored cover letters based on:
- Specific job title and company
- Your CV information
- Industry standards and best practices
- Company research and culture fit

**Format:** `/coverletter [Job Title] | [Company Name]`

**Examples:**
```
/coverletter Software Engineer | Google
/coverletter Marketing Manager | Apple
/coverletter Data Scientist | Remote Company
```

**Features:**
- Customized to job requirements
- Highlights relevant experience
- Professional tone and structure
- Editable template output

**Premium Feature** — unlocked by default with `ENABLE_PREMIUM=true`.

---

### 💎 Premium Features

With `ENABLE_PREMIUM=true` (default in self-hosted mode), all features are unlocked:

- Unlimited job searches
- Up to 20 active job alerts
- AI CV review
- Cover letter generator
- Mock interview practice
- Full search results access
- Enhanced career insights

---

### ℹ️ Help & Information

#### `/start`
Initializes the bot and displays welcome message with overview.

#### `/subscribe`
Shows subscription options (only if `ENABLE_PAYMENTS=true`).

---

## Features

### Smart Job Search
- **Natural Language Processing**: Understands complex queries like "senior python jobs in tech startups"
- **Multi-platform Aggregation**: Searches across multiple job boards (JSearch, Adzuna, Careerjet, Findwork, Jooble, Arbeitnow, Remotive, Jobicy, Authentic Jobs)
- **Advanced Filtering**: Location, salary, experience level, company size, and more
- **Relevance Scoring**: AI-powered matching based on your profile and preferences

### Professional CV Builder
- **Guided Creation**: Step-by-step process for each CV section
- **Industry Templates**: Field-specific formats (tech, marketing, healthcare, etc.)
- **ATS Optimization**: Ensures compatibility with applicant tracking systems
- **Export Options**: Multiple format support
- **AI Review**: Get feedback on your CV (Premium)

### Intelligent Job Alerts
- **Automated Monitoring**: Checks every 30 minutes for new matching positions
- **Instant Notifications**: Receive alerts via Telegram
- **Customizable Criteria**: Set specific requirements for your ideal job
- **Multiple Alerts**: Create up to 20 alerts (Premium) or 5 (Free)

### Career Development Tools
- **Career Path Explorer**: Discover progression opportunities and related roles
- **Upskill Plans**: Get personalized learning roadmaps
- **Mock Interviews**: Practice with AI-powered interview sessions (Premium)
- **Cover Letter Generator**: Create tailored cover letters (Premium)

---

## Using the Bots

### Telegram Bot

**Starting the Bot**:
1. Search for your bot in Telegram
2. Click "Start" or type `/start`

**Available Commands**:
- `/start` - Initialize the bot
- `/findjobs <query>` - Search for jobs
- `/setalert` - Create job alerts
- `/myalerts` - Manage job alerts
- `/history` - View saved jobs
- `/build_cv` - Create your CV
- `/view_cv` - View your CV
- `/cv_review` - Get CV feedback (Premium)
- `/coverletter <title> | <company>` - Generate cover letter (Premium)
- `/careerpath <role>` - Explore career paths
- `/upskill` - Get learning recommendations
- `/practice` - Mock interview practice (Premium)
- `/quota` - Check remaining searches
- `/subscribe` - Manage subscription (if payments enabled)

**Tips**:
- You can search by typing `/findjobs` followed by your query
- Save jobs directly from search results
- Get notified about new jobs matching your alerts

### WhatsApp Bot

**Starting the Bot**:
1. Save the Job Bot number to your contacts
2. Send "Hi" or "Start" to begin

**Available Commands**:
Same as Telegram - just type the command (e.g., `/findjobs python developer`)

**Tips**:
- WhatsApp bot works exactly like Telegram
- All your data is stored in the same database

### Bot Best Practices

1. **Be Specific**: Use detailed search queries for better results
   - ❌ `/findjobs developer`
   - ✅ `/findjobs senior python developer remote`

2. **Use Alerts**: Set up alerts for ongoing job searches
   - Save time by getting notified automatically
   - Focus on jobs that match your criteria

---

## REST API

The REST API is available for scripts, automation, or custom frontends.

### Authentication

All API requests require a Bearer token:

```bash
curl -H "Authorization: Bearer YOUR_API_TOKEN" \
  http://127.0.0.1:8000/api/user/profile/
```

### Interactive Documentation

OpenAPI/Swagger docs are auto-generated:

| URL | Description |
|-----|-------------|
| `/api/schema/` | OpenAPI schema (JSON) |
| `/api/docs/` | Swagger UI |
| `/api/redoc/` | ReDoc UI |

### Key Endpoints

```
GET   /api/user/profile/          Get user profile
PATCH /api/user/profile/          Update user profile
POST  /api/jobs/search/           Search for jobs
GET   /api/jobs/saved/            Get saved jobs
POST  /api/jobs/saved/            Save a job
GET   /api/alerts/                List alerts
POST  /api/alerts/                Create alert
POST  /api/alerts/{id}/toggle/    Toggle alert
POST  /api/career/path/           Get career path
POST  /api/career/upskill/        Get upskill plan
POST  /api/interview/practice/    Interview practice
GET   /api/interview/session/     Check session
POST  /api/cv/review/             CV review
POST  /api/cv/coverletter/        Cover letter
GET   /api/subscription/quota/    Get quota
```

---

## Feature Flags

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_PREMIUM` | `true` | Unlocks all premium features (CV review, cover letters, interview practice, unlimited searches) |
| `ENABLE_PAYMENTS` | `false` | Enables Paystack/Flutterwave payment integration |

When `ENABLE_PREMIUM=true`, all features are unlocked regardless of subscription status.

When `ENABLE_PAYMENTS=false`, subscription endpoints return `501 Not Implemented`.

---

## FAQ

### General Questions

**Q: Is Job Bot free?**
A: Yes! In self-hosted mode, `ENABLE_PREMIUM=true` unlocks all features by default.

**Q: Which platforms does Job Bot support?**
A: Job Bot is available on Telegram (primary), WhatsApp (optional), and via REST API.

**Q: Which job boards do you search?**
A: We aggregate from multiple sources including JSearch, Adzuna, Careerjet, Findwork, Jooble, Arbeitnow, Remotive, Jobicy, and Authentic Jobs.

### Job Search

**Q: How accurate are the job matches?**
A: Job Bot uses advanced AI algorithms to match your profile with relevant positions, considering skills, experience, preferences, and career goals.

**Q: Can I apply directly through Job Bot?**
A: We provide direct links to job applications. Click "Apply Now" to go to the employer's application page.

**Q: How do I save a job?**
A: Click the "Save" button in bot search results.

### Alerts

**Q: How often do I get alert notifications?**
A: Alerts check for new positions every 30 minutes and notify you when matches are found.

**Q: Can I pause an alert?**
A: Yes! Use `/myalerts` in the bot to toggle alerts on/off.

**Q: How many alerts can I create?**
A: Free plan: 5 alerts. Premium plan (ENABLE_PREMIUM=true): Up to 20 alerts.

### CV & Applications

**Q: Can I export my CV?**
A: Yes, the CV builder allows export in multiple formats suitable for different applications.

**Q: How does the CV review work?**
A: Our AI analyzes your CV and provides feedback on content, formatting, and optimization for job applications (Premium feature).

**Q: Can I generate multiple cover letters?**
A: Yes! Premium users can generate unlimited cover letters for different job applications.

### Technical Issues

**Q: The bot isn't responding. What should I do?**
A:
1. Check your internet connection
2. Try typing `/start` to restart the bot
3. Check that the bot is running (`python manage.py run_bot`)
4. Check server logs

**Q: My search quota isn't updating. Why?**
A:
1. Check your `ENABLE_PREMIUM` setting
2. Check your subscription status
3. Contact support if the issue persists

**Q: Is there a mobile app?**
A: Job Bot runs entirely within Telegram and WhatsApp, which are available on all major mobile platforms.

---

## Support

### Getting Help
- **In-Bot Support**: Use `/start` for command assistance
- **Documentation**: See `docs/` in the repository
- **Source Code**: [github.com/pluggedspace/Job-bot](https://github.com/pluggedspace/Job-bot)

### Common Issues
- **Search Limits**: Use `/quota` to check remaining searches
- **CV Building**: Use `/build_cv` for step-by-step guidance
- **Job Alerts**: Use `/myalerts` to manage notifications
- **Premium Features**: Set `ENABLE_PREMIUM=true` in `.env`

---

## Tips for Success

### Optimize Your Job Search

1. **Use Specific Keywords**: Include job title, skills, and location
2. **Set Up Alerts**: Don't miss out on new opportunities
3. **Update Your Profile**: Keep your CV current
4. **Apply Quickly**: Early applications get more attention

### Make the Most of Premium

1. **Review Your CV**: Get AI feedback before applying
2. **Customize Cover Letters**: Generate tailored letters for each application
3. **Practice Interviews**: Build confidence with mock interviews
4. **Explore Career Paths**: Plan your long-term career growth

### Stay Organized

1. **Save Interesting Jobs**: Build your job pipeline
2. **Track Applications**: Keep notes on where you've applied
3. **Follow Up**: Check application status regularly
4. **Network**: Connect with people in your target companies

---

**Happy Job Hunting! 🎉**

We're here to help you find your dream job. Good luck!

---

*Last updated: August 2026*  
*Version: 3.0*  
*For the latest updates, visit the repository.*
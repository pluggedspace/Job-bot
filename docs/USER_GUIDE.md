# Job Bot - User Guide

Welcome to Job Bot! Your AI-powered job search assistant available on web, Telegram, and WhatsApp.

**Version**: 2.1  
**Last Updated**: December 2025

## Table of Contents
- [Overview](#overview)
- [Getting Started](#getting-started)
- [Commands Reference](#commands-reference)
- [Features](#features)
- [Using the Bots](#using-the-bots)
- [Subscription Plans](#subscription-plans)
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

**Target Audience**: Job seekers at all career levels, from entry-level to experienced professionals.

---

## Getting Started

### Creating an Account

#### Web Application
1. Visit the Job Bot website
2. Click "Sign Up" or "Register"
3. Fill in your details:
   - Email address
   - Password
   - First and last name
   - Organization name
4. Click "Create Account"
5. You're ready to start!

#### Telegram Bot
1. Open Telegram
2. Search for `@jobautobot` or visit [t.me/jobautobot](https://t.me/jobautobot)
3. Click "Start" or type `/start`
4. The bot will create your account automatically
5. Start searching for jobs!

#### WhatsApp Bot
1. Open WhatsApp
2. Send a message to the Job Bot number
3. Type "Hi" or "Start"
4. The bot will create your account automatically
5. Start searching for jobs!

### Linking Your Accounts

Connect your web, Telegram, and WhatsApp accounts to sync your data:

1. **Get Your Linking Code**:
   - In Telegram or WhatsApp, type `/link`
   - You'll receive a 6-character code (e.g., ABC123)
   - This code expires in 10 minutes

2. **Link on Web**:
   - Log in to the web app
   - Go to "Link Accounts" page
   - Enter your 6-character code
   - Click "Link Account"

3. **Benefits**:
   - Unified job alerts across all platforms
   - Shared subscription and search quota
   - Access your CV and saved jobs anywhere
   - Seamless experience across devices

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

**Web Alternative**: Use the "Job Search" page with the search form.

#### `/quota`
Shows your remaining job searches for the current month.

- **Free Users:** 10 searches per month
- **Premium Users:** Unlimited searches

**Web Alternative**: Check the "Subscription" page for your quota.

#### `/history`
Displays your saved jobs and search history.

**Web Alternative**: View saved jobs on the "Job Search" page.

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

**Web Alternative**: Use the "CV Builder" page to edit your profile.

#### `/view_cv`
Displays your current CV in a formatted, readable layout.

**Web Alternative**: View your profile on the "CV Builder" page.

#### `/cv_review`
Provides AI-powered analysis of your CV with suggestions for:
- Formatting improvements
- Content optimization
- Keyword enhancement for ATS systems
- Section organization

**Premium Feature** - Available on web "CV Builder" page.

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

**Web Alternative**: Use the "Job Alerts" page to create and manage alerts.

#### `/myalerts`
Manages your active job alerts:
- View all active alerts
- Edit alert criteria
- Delete alerts
- Pause/resume alerts

**Web Alternative**: Manage alerts on the "Job Alerts" page.

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

**Web Alternative**: Use the "Career Path" page.

#### `/practice`
Interactive interview preparation with:
- Common behavioral questions
- Technical questions by field
- STAR method guidance
- Sample answers and feedback

**Premium Feature** - Available on web "Interview Practice" page.

#### `/upskill`
Generates personalized learning recommendations:
- Skill gaps analysis
- Online course suggestions with links
- Reading materials
- Project ideas
- Certification paths

**Web Alternative**: Use the "Upskill Plan" page.

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

**Premium Feature** - Available on web "CV Builder" page.

---

### 💎 Premium Features

#### `/subscribe`
Shows premium plan options and upgrade process.

**Premium Benefits:**
- Unlimited job searches (vs. 10/month free)
- Up to 5 active job alerts (vs. 1 free)
- AI CV review
- Cover letter generator
- Mock interview practice
- Priority support
- Full search results access
- Enhanced career insights

**Web Alternative**: Visit the "Subscription" page to upgrade.

---

### ℹ️ Help & Information

#### `/start`
Initializes the bot and displays welcome message with overview.

#### `/help`
Lists all available commands with brief descriptions.

#### `/link`
Generates a linking code to connect your bot account to the web app.

#### `/unlink`
Disconnects your bot account from the web app.

---

## Features

### Smart Job Search
- **Natural Language Processing**: Understands complex queries like "senior python jobs in tech startups"
- **Multi-platform Aggregation**: Searches across major job boards (LinkedIn, Indeed, Glassdoor, etc.)
- **Advanced Filtering**: Location, salary, experience level, company size, and more
- **Relevance Scoring**: AI-powered matching based on your profile and preferences

### Professional CV Builder
- **Guided Creation**: Step-by-step process for each CV section
- **Industry Templates**: Field-specific formats (tech, marketing, healthcare, etc.)
- **ATS Optimization**: Ensures compatibility with applicant tracking systems
- **Export Options**: Multiple format support
- **AI Review**: Get feedback on your CV (Premium)

### Intelligent Job Alerts
- **Automated Monitoring**: Daily checks for new matching positions
- **Instant Notifications**: Receive alerts via Telegram, WhatsApp, or email
- **Customizable Criteria**: Set specific requirements for your ideal job
- **Multiple Alerts**: Create up to 5 alerts (Premium) or 1 (Free)

### Career Development Tools
- **Career Path Explorer**: Discover progression opportunities and related roles
- **Upskill Plans**: Get personalized learning roadmaps
- **Mock Interviews**: Practice with AI-powered interview sessions (Premium)
- **Cover Letter Generator**: Create tailored cover letters (Premium)

### Career Analytics
- **Search Tracking**: Monitors your job search activity and patterns
- **Skill Gap Analysis**: Identifies areas for professional development
- **Market Insights**: Provides industry trends and salary data

---

## Using the Bots

### Telegram Bot

**Starting the Bot**:
1. Search for `@jobautobot` in Telegram or visit [t.me/jobautobot](https://t.me/jobautobot)
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
- `/link` - Generate linking code
- `/unlink` - Disconnect from web account
- `/subscribe` - Manage subscription
- `/help` - Get help

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
- All your data syncs across platforms
- You can switch between platforms anytime

### Bot Best Practices

1. **Be Specific**: Use detailed search queries for better results
   - ❌ `/findjobs developer`
   - ✅ `/findjobs senior python developer remote`

2. **Use Alerts**: Set up alerts for ongoing job searches
   - Save time by getting notified automatically
   - Focus on jobs that match your criteria

3. **Link Accounts**: Connect your web and bot accounts
   - Access premium features on all platforms
   - Keep your data synchronized

---

## Subscription Plans

### Free Plan

**Included**:
- ✅ 10 job searches per month
- ✅ 1 job alert
- ✅ Save unlimited jobs
- ✅ Basic CV building
- ✅ Career path explorer
- ✅ Upskill learning plans
- ✅ Access via web, Telegram, and WhatsApp

**Limitations**:
- ❌ Limited searches (10/month)
- ❌ Only 1 alert
- ❌ No CV review
- ❌ No cover letter generator
- ❌ No mock interviews

### Premium Plan

**Price**: NGN 4,500/month (approximately $9.99 USD)

**Everything in Free, Plus**:
- ✅ **Unlimited job searches**
- ✅ **Up to 5 job alerts**
- ✅ **AI CV review**
- ✅ **Cover letter generator**
- ✅ **Mock interview practice**
- ✅ **Priority support**
- ✅ **Full search results access**
- ✅ **Enhanced career insights**
- ✅ **Early access to new features**

### How to Subscribe

1. **Via Web**:
   - Go to "Subscription" page
   - Click "Upgrade to Premium"
   - Complete payment via Paystack
   - Verify payment

2. **Via Bot**:
   - Type `/subscribe`
   - Follow the payment instructions
   - Your account will be upgraded automatically

### Payment Methods

- **Paystack**: Credit/Debit cards, Bank transfer
- **Secure**: All payments are processed securely
- **Cancel Anytime**: No long-term commitment

---

## FAQ

### General Questions

**Q: Is Job Bot free?**
A: Yes! We offer a free plan with 10 searches per month. Premium plans unlock unlimited searches and advanced features.

**Q: Which platforms does Job Bot support?**
A: Job Bot is available on web, Telegram, and WhatsApp. You can use any or all platforms.

**Q: Can I use Job Bot on multiple devices?**
A: Yes! Link your accounts to access your data across all platforms and devices.

**Q: Which job boards do you search?**
A: We aggregate from multiple sources including LinkedIn, Indeed, Glassdoor, major job boards, company career pages, and specialized platforms.

### Account & Linking

**Q: How do I link my Telegram/WhatsApp to my web account?**
A: Type `/link` in the bot to get a 6-character code. Enter this code on the web app's "Link Accounts" page.

**Q: What happens when I link my accounts?**
A: Your job alerts, saved jobs, subscription status, and search quota are shared across all platforms.

**Q: Can I unlink my accounts?**
A: Yes, use the "Unlink" button on the web app or type `/unlink` in the bot.

**Q: Is my data secure?**
A: Yes, we take data privacy seriously. Your personal information and CV data are encrypted and stored securely.

### Job Search

**Q: How accurate are the job matches?**
A: Job Bot uses advanced AI algorithms to match your profile with relevant positions, considering skills, experience, preferences, and career goals.

**Q: Can I apply directly through Job Bot?**
A: We provide direct links to job applications. Click "Apply Now" to go to the employer's application page.

**Q: How do I save a job?**
A: Click the "Save" button on web or use the save option in bot search results.

### Alerts

**Q: How often do I get alert notifications?**
A: Alerts check for new positions daily and notify you immediately when matches are found.

**Q: Can I pause an alert?**
A: Yes! Use the "Pause" button on web or manage alerts via `/myalerts` in the bot.

**Q: How many alerts can I create?**
A: Free plan: 1 alert. Premium plan: Up to 5 alerts.

### CV & Applications

**Q: Can I export my CV?**
A: Yes, the CV builder allows export in multiple formats suitable for different applications.

**Q: How does the CV review work?**
A: Our AI analyzes your CV and provides feedback on content, formatting, and optimization for job applications (Premium feature).

**Q: Can I generate multiple cover letters?**
A: Yes! Premium users can generate unlimited cover letters for different job applications.

### Subscription

**Q: Is there a free trial for premium?**
A: All users start with free access. Premium features are available through subscription with clear benefits outlined.

**Q: How do I upgrade to Premium?**
A: Go to the "Subscription" page on web or type `/subscribe` in the bot.

**Q: What payment methods do you accept?**
A: We accept credit/debit cards and bank transfers via Paystack.

**Q: Can I cancel my subscription?**
A: Yes, you can cancel anytime. Your premium features will remain active until the end of your billing period.

**Q: Do I get a refund if I cancel?**
A: Subscriptions are non-refundable, but you can use premium features until the end of your billing period.

### Technical Issues

**Q: The bot isn't responding. What should I do?**
A: 
1. Check your internet connection
2. Try typing `/start` to restart the bot
3. If the issue persists, contact support

**Q: I didn't receive my linking code. What should I do?**
A: Type `/link` again to generate a new code. Codes expire after 10 minutes.

**Q: My search quota isn't updating. Why?**
A: 
1. Ensure your accounts are linked if using multiple platforms
2. Check your subscription status
3. Contact support if the issue persists

**Q: I can't log in to the web app. What should I do?**
A:
1. Verify your email and password
2. Try resetting your password
3. Clear your browser cache
4. Contact support if needed

**Q: Is there a mobile app?**
A: Job Bot runs entirely within Telegram and WhatsApp, which are available on all major mobile platforms. The web app is also mobile-responsive.

---

## Support

### Getting Help
- **In-Bot Support**: Use `/help` for command assistance
- **Email**: support@pluggedspace.org
- **Documentation**: [docs.pluggedspace.org/models/job](https://docs.pluggedspace.org/models/job)
- **Website**: [pluggedspace.org/projects/job](https://pluggedspace.org/projects/job)

### Common Issues
- **Search Limits**: Use `/quota` to check remaining searches
- **CV Building**: Use `/build_cv` for step-by-step guidance
- **Job Alerts**: Use `/myalerts` to manage notifications
- **Premium Features**: Use `/subscribe` for upgrade information

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

*Last updated: December 2024*  
*Version: 2.1*  
*For the latest updates, visit our documentation site.*

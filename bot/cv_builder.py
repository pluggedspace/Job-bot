from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
)
from docx import Document
import os
from asgiref.sync import sync_to_async
from bot.models import User

# Extended conversation states
(
    NAME, TITLE, EMAIL, PHONE, LOCATION, LINKS, SUMMARY,
    EDUCATION, ADD_EDUCATION, EXPERIENCE, ADD_EXPERIENCE,
    CERTIFICATIONS, ADD_CERTIFICATIONS,
    LANGUAGES, AWARDS, ADD_AWARDS,
    REFEREES, ADD_REFEREES, SKILLS
) = range(19)


async def start_cv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None:
        return ConversationHandler.END

    context.user_data.clear()
    context.user_data['education'] = []
    context.user_data['experience'] = []
    context.user_data['certifications'] = []
    context.user_data['awards'] = []
    context.user_data['referees'] = []

    await update.message.reply_text(
        "👋 *Let's build your professional CV!* \n\n"
        "I'll ask you a few questions to create a stunning resume.\n"
        "First, what is your *Full Name*?",
        parse_mode='Markdown'
    )
    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['name'] = update.message.text
    await update.message.reply_text(
        "Great! What is your *Current Professional Title*? (e.g., Software Engineer, Marketing Manager)",
        parse_mode='Markdown'
    )
    return TITLE


async def get_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['title'] = update.message.text
    await update.message.reply_text("📧 What is your *Email Address*?", parse_mode='Markdown')
    return EMAIL


async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['email'] = update.message.text
    await update.message.reply_text("📱 What is your *Phone Number*?", parse_mode='Markdown')
    return PHONE


async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['phone'] = update.message.text
    await update.message.reply_text("🌍 What is your *City and Country* of residence?", parse_mode='Markdown')
    return LOCATION


async def get_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['location'] = update.message.text
    await update.message.reply_text(
        "🔗 Please provide your *Professional Links* (LinkedIn, Portfolio, etc.), separated by commas:",
        parse_mode='Markdown'
    )
    return LINKS


async def get_links(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['links'] = [l.strip() for l in update.message.text.split(',')]
    await update.message.reply_text(
        "📝 Write a *Brief Professional Summary* (2-3 sentences about your experience and goals):",
        parse_mode='Markdown'
    )
    return SUMMARY


async def get_summary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['summary'] = update.message.text
    await update.message.reply_text(
        "🎓 Let's add your *Education*.\n"
        "Please enter an entry in this format:\n"
        "_Degree, University, Year_",
        parse_mode='Markdown'
    )
    return EDUCATION


async def get_education(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['education'].append(update.message.text)
    await update.message.reply_text("Do you want to add another education entry? (yes/no)")
    return ADD_EDUCATION


async def add_education(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text.lower() == 'yes':
        await update.message.reply_text("Enter the next education entry:")
        return EDUCATION
    await update.message.reply_text(
        "💼 Now, let's add your *Work Experience*.\n"
        "Please enter your most recent role:\n"
        "_Role, Company, Duration (e.g. 2020-Present)_",
        parse_mode='Markdown'
    )
    return EXPERIENCE


async def get_experience(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['experience'].append(update.message.text)
    await update.message.reply_text("Add another work experience entry? (yes/no)")
    return ADD_EXPERIENCE


async def add_experience(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text.lower() == 'yes':
        await update.message.reply_text("Enter the next work experience:")
        return EXPERIENCE
    await update.message.reply_text(
        "📜 Do you have any *Certifications*? (e.g., PMP, AWS Certified)\n"
        "Enter one, or type 'skip' if none.",
        parse_mode='Markdown'
    )
    return CERTIFICATIONS


async def get_certifications(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if text.lower() != 'skip':
        context.user_data['certifications'].append(text)
        await update.message.reply_text("Add another certification? (yes/no)")
        return ADD_CERTIFICATIONS
    
    await update.message.reply_text("🗣️ What *Languages* do you speak? (comma-separated)", parse_mode='Markdown')
    return LANGUAGES


async def add_certifications(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text.lower() == 'yes':
        await update.message.reply_text("Enter the next certification:")
        return CERTIFICATIONS
    await update.message.reply_text("🗣️ What *Languages* do you speak? (comma-separated)", parse_mode='Markdown')
    return LANGUAGES


async def get_languages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['languages'] = [l.strip() for l in update.message.text.split(',')]
    await update.message.reply_text(
        "🏆 Any *Awards or Achievements*?\n"
        "Enter one, or type 'skip' if none.",
        parse_mode='Markdown'
    )
    return AWARDS


async def get_awards(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if text.lower() != 'skip':
        context.user_data['awards'].append(text)
        await update.message.reply_text("Add another award? (yes/no)")
        return ADD_AWARDS
    
    await update.message.reply_text(
        "👥 Please add a *Referee*:\n"
        "_Name, Position, Contact Info_",
        parse_mode='Markdown'
    )
    return REFEREES


async def add_awards(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text.lower() == 'yes':
        await update.message.reply_text("Enter the next award:")
        return AWARDS
    await update.message.reply_text(
        "👥 Please add a *Referee*:\n"
        "_Name, Position, Contact Info_",
        parse_mode='Markdown'
    )
    return REFEREES


async def get_referees(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['referees'].append(update.message.text)
    await update.message.reply_text("Add another referee? (yes/no)")
    return ADD_REFEREES


async def add_referees(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text.lower() == 'yes':
        await update.message.reply_text("Enter the next referee:")
        return REFEREES
    await update.message.reply_text(
        "💡 Finally, list your *Key Skills* (comma-separated):\n"
        "_e.g., Python, Project Management, SEO_",
        parse_mode='Markdown'
    )
    return SKILLS


async def get_skills(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    d = context.user_data
    d['skills'] = [s.strip() for s in update.message.text.split(',')]

    user = await sync_to_async(User.objects.get)(user_id=str(update.effective_user.id))
    user.cv_data = d
    user.current_job_title = d['title']
    user.skills = d['skills']
    await sync_to_async(user.save)()

    await sync_to_async(user.save)()
    
    await update.message.reply_text("✨ *Generating your professional CV...* Please wait a moment.", parse_mode='Markdown')

    # Create CV Document
    doc = Document()
    doc.add_heading(d['name'], 0)
    doc.add_paragraph(d['title'])
    doc.add_paragraph(f"{d['email']} | {d['phone']} | {d['location']}")

    if d.get('links'):
        doc.add_heading("Links", level=1)
        for link in d['links']:
            doc.add_paragraph(link, style='List Bullet')

    doc.add_heading("Professional Summary", level=1)
    doc.add_paragraph(d['summary'])

    doc.add_heading("Education", level=1)
    for edu in d['education']:
        doc.add_paragraph(edu, style='List Bullet')

    doc.add_heading("Experience", level=1)
    for exp in d['experience']:
        doc.add_paragraph(exp, style='List Bullet')

    doc.add_heading("Certifications", level=1)
    for cert in d['certifications']:
        doc.add_paragraph(cert, style='List Bullet')

    doc.add_heading("Languages", level=1)
    for lang in d['languages']:
        doc.add_paragraph(lang, style='List Bullet')

    doc.add_heading("Awards", level=1)
    for award in d['awards']:
        doc.add_paragraph(award, style='List Bullet')

    doc.add_heading("Referees", level=1)
    for ref in d['referees']:
        doc.add_paragraph(ref, style='List Bullet')

    doc.add_heading("Skills", level=1)
    for skill in d['skills']:
        doc.add_paragraph(skill, style='List Bullet')

    filename = f"{d['name'].replace(' ', '_')}_cv.docx"
    doc.save(filename)
    with open(filename, 'rb') as f:
        await update.message.reply_document(
            document=f,
            caption="✅ *Here is your new CV!* \nGood luck with your job search! 🚀",
            parse_mode='Markdown'
        )
    os.remove(filename)

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is not None:
        await update.message.reply_text("CV building canceled.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def get_cv_handler():
    return ConversationHandler(
        entry_points=[
            CommandHandler('build_cv', start_cv),
            CommandHandler('cv', start_cv),
        ],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_title)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_location)],
            LINKS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_links)],
            SUMMARY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_summary)],
            EDUCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_education)],
            ADD_EDUCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_education)],
            EXPERIENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_experience)],
            ADD_EXPERIENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_experience)],
            CERTIFICATIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_certifications)],
            ADD_CERTIFICATIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_certifications)],
            LANGUAGES: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_languages)],
            AWARDS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_awards)],
            ADD_AWARDS: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_awards)],
            REFEREES: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_referees)],
            ADD_REFEREES: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_referees)],
            SKILLS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_skills)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
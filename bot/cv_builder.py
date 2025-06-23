from telegram import Update, ReplyKeyboardRemove 
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
)
from docx import Document 
import os

# Conversation states
(NAME, TITLE, EMAIL, PHONE, SUMMARY, EDUCATION, ADD_EDUCATION, EXPERIENCE, ADD_EXPERIENCE, SKILLS) = range(10)

async def start_cv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the CV building conversation."""
    if update.message is None:
        return ConversationHandler.END
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    context.user_data.clear()
    context.user_data['education'] = []
    context.user_data['experience'] = []
    await update.message.reply_text("Let's build your CV. What's your full name?")
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None or update.message.text is None:
        return ConversationHandler.END
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Professional Title?")
    return TITLE

async def get_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None or update.message.text is None:
        return ConversationHandler.END
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    context.user_data['title'] = update.message.text
    await update.message.reply_text("Email?")
    return EMAIL

async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None or update.message.text is None:
        return ConversationHandler.END
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    context.user_data['email'] = update.message.text
    await update.message.reply_text("Phone Number?")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None or update.message.text is None:
        return ConversationHandler.END
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    context.user_data['phone'] = update.message.text
    await update.message.reply_text("Brief professional summary:")
    return SUMMARY

async def get_summary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None or update.message.text is None:
        return ConversationHandler.END
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    context.user_data['summary'] = update.message.text
    await update.message.reply_text("Enter an education entry (e.g., BSc in XYZ, Uni Name, Year):")
    return EDUCATION

async def get_education(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None or update.message.text is None:
        return ConversationHandler.END
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    context.user_data['education'].append(update.message.text)
    await update.message.reply_text("Add another education entry? (yes/no)")
    return ADD_EDUCATION

async def add_education(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None or update.message.text is None:
        return ConversationHandler.END
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    if update.message.text.lower() == 'yes':
        await update.message.reply_text("Enter next education entry:")
        return EDUCATION
    else:
        await update.message.reply_text("Now enter a work experience (e.g., Role, Company, Years, Responsibilities):")
        return EXPERIENCE

async def get_experience(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None or update.message.text is None:
        return ConversationHandler.END
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    context.user_data['experience'].append(update.message.text)
    await update.message.reply_text("Add another work experience entry? (yes/no)")
    return ADD_EXPERIENCE

async def add_experience(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None or update.message.text is None:
        return ConversationHandler.END
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    if update.message.text.lower() == 'yes':
        await update.message.reply_text("Enter next work experience:")
        return EXPERIENCE
    else:
        await update.message.reply_text("List your skills (comma-separated):")
        return SKILLS

async def get_skills(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None or update.message.text is None:
        return ConversationHandler.END
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    context.user_data['skills'] = [s.strip() for s in update.message.text.split(',')]
    await update.message.reply_text("Generating your CV...")
    # Generate CV document
    d = context.user_data
    doc = Document()
    doc.add_heading(d['name'], 0)
    doc.add_paragraph(d['title'])
    doc.add_paragraph(f"{d['email']} | {d['phone']}")
    doc.add_paragraph("\n")
    doc.add_heading("Professional Summary", level=1)
    doc.add_paragraph(d['summary'])
    doc.add_heading("Education", level=1)
    for edu in d['education']:
        doc.add_paragraph(edu, style='List Bullet')
    doc.add_heading("Experience", level=1)
    for exp in d['experience']:
        doc.add_paragraph(exp, style='List Bullet')
    doc.add_heading("Skills", level=1)
    for skill in d['skills']:
        doc.add_paragraph(skill, style='List Bullet')
    filename = f"{d['name'].replace(' ', '_')}_cv.docx"
    doc.save(filename)
    with open(filename, 'rb') as f:
        await update.message.reply_document(f)
    os.remove(filename)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None:
        return ConversationHandler.END
    await update.message.reply_text("CV building canceled.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def get_cv_handler():
    """Return the ConversationHandler for the CV builder."""
    return ConversationHandler(
        entry_points=[
            CommandHandler('build_cv', start_cv),
            CommandHandler('cv', start_cv),  # Alias for /cv
        ],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_title)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            SUMMARY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_summary)],
            EDUCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_education)],
            ADD_EDUCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_education)],
            EXPERIENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_experience)],
            ADD_EXPERIENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_experience)],
            SKILLS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_skills)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )


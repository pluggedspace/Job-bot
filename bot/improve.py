import json
import os
from typing import Optional
from bot.models import User
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage

# Load AI API Key securely
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
if not MISTRAL_API_KEY:
    raise ValueError("Missing MISTRAL_API_KEY environment variable")

# Initialize AI Client
client = MistralClient(api_key=MISTRAL_API_KEY)
MODEL = "mistral-tiny"  # You can change to mistral-small or mistral-medium


def call_ai(prompt: str, system_prompt: str = "You are a helpful assistant.") -> str:
    """
    Sends a prompt to Mistral and returns the generated response text.
    """
    messages = [
        ChatMessage(role="system", content=system_prompt),
        ChatMessage(role="user", content=prompt)
    ]

    try:
        response = client.chat(
            model=MODEL,
            messages=messages,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ Error while generating response: {str(e)}"


def generate_cover_letter(
    user: User,
    job_title: str,
    company_name: Optional[str] = None,
    job_description: Optional[str] = None,
    tone: str = "Formal"
) -> dict:
    """
    Generates a personalized cover letter using user's stored data.
    Returns either a completed letter or a list of missing profile fields.
    """

    # Collect user data
    cv = user.cv_data or {}
    current_title = user.current_job_title
    skills = user.skills or []
    name = user.username or "Applicant"

    # Validate data
    missing = []
    if not cv:
        missing.append("CV data")
    if not current_title:
        missing.append("current job title")
    if not skills:
        missing.append("skills")

    if missing:
        return {
            "error": True,
            "missing_fields": missing,
            "message": f"You're missing the following from your profile: {', '.join(missing)}. Use /cv_builder or /update_profile to fix this."
        }

    # Build optional job description string
    job_desc_text = f"\nJob Description:\n{job_description}" if job_description else ""

    # Construct prompt
    prompt = f"""
Act as a professional recruiter writing a tailored {tone.lower()} cover letter.

Role: {job_title}
Company: {company_name or '[Company Not Provided]'}

User Details:
- Name: {name}
- Current Job Title: {current_title}
- Skills: {', '.join(skills)}
- CV: {json.dumps(cv, indent=2)}{job_desc_text}

Write a concise letter (max 250 words) that includes:
- A strong introduction
- Key qualifications
- Reason for interest in the role/company
- A confident closing
    """

    # Generate letter
    letter = call_ai(prompt)

    return {
        "error": False,
        "job_title": job_title,
        "company": company_name,
        "tone": tone,
        "cover_letter": letter
    }


def review_cv(user: User) -> dict:
    """
    Reviews the user's CV data and gives feedback on strengths, weaknesses, and improvements.
    """

    # Collect user data
    cv = user.cv_data or {}
    current_title = user.current_job_title
    skills = user.skills or []

    # Validate data
    missing = []
    if not cv:
        missing.append("CV data")
    if not current_title:
        missing.append("current job title")
    if not skills:
        missing.append("skills")

    if missing:
        return {
            "error": True,
            "missing_fields": missing,
            "message": f"You're missing the following from your profile: {', '.join(missing)}. Use /cv_builder or /update_profile to fix this."
        }

    # Construct prompt
    prompt = f"""
You're a professional CV reviewer.

Evaluate the CV data below and return:
1. Summary of strengths
2. Grammar, formatting, or structure issues
3. Suggestions to improve relevance, clarity, and professionalism

User Details:
- Current Job Title: {current_title}
- Skills: {', '.join(skills)}
- CV Content: {json.dumps(cv, indent=2)}
    """

    # Generate review
    review = call_ai(prompt)

    return {
        "error": False,
        "cv_review": review
    }
import json
import os
from typing import Optional
from bot.models import User
from mistralai import Mistral

# Load AI API Key securely
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
if not MISTRAL_API_KEY:
    raise ValueError("Missing MISTRAL_API_KEY environment variable")

# Initialize AI Client
client = Mistral(api_key=MISTRAL_API_KEY)
MODEL = "mistral-tiny"  # You can change to mistral-small or mistral-medium


def call_ai(prompt: str, system_prompt: str = "You are a helpful assistant.") -> str:
    """
    Sends a prompt to Mistral and returns the generated response text.
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    try:
        response = client.chat.complete(
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
    
    # Extract more details from CV if available
    experience = cv.get('experience', [])
    summary = cv.get('summary', '')

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

    # Build context strings
    company_str = company_name or "the hiring company"
    job_desc_str = f"Job Description/Requirements:\n{job_description}" if job_description else "Target Role: Standard requirements for this position."
    skills_str = ', '.join(skills)
    
    # Construct a robust prompt
    prompt = f"""
    You are an expert Career Coach and Professional Resume Writer with massive experience in ATS (Applicant Tracking Systems). 
    Your task is to write a high-converting, ATS-friendly cover letter for the following candidate.

    --- CANDIDATE PROFILE ---
    Name: {name}
    Current Role: {current_title}
    Professional Summary: {summary}
    Top Skills: {skills_str}
    Recent Experience: {experience[:2] if experience else "Not specified"}

    --- TARGET ROLE ---
    Job Title: {job_title}
    Company: {company_str}
    {job_desc_str}

    --- INSTRUCTIONS ---
    Tone: {tone} (Professional, Confident, and Engaging)
    Format: Clean, standard business letter format.
    Length: 200-300 words (concise and impactful).

    Content Requirements:
    1. **Header**: Do NOT include a fake address header. Start with "Dear Hiring Manager," (or specific name if known).
    2. **Opening**: Strong hook. State clearly why you are applying and tailored enthusiasm for {company_str}.
    3. **Body Paragraph 1 (The "Why You")**: Highlight specific achievements from the candidate's profile that match the job requirements. Use metrics/numbers if available in the profile. Connect skills ({skills_str}) to the role.
    4. **Body Paragraph 2 (The "Why Them")**: briefly mention why this specific role/company is the right next step.
    5. **Closing**: Strong call to action (e.g., "I look forward to discussing how my skills in X and Y can benefit your team...").
    6. **Sign-off**: "Sincerely,\n{name}"

    **CRITICAL**: 
    - Use keywords from the job description naturally for ATS optimization.
    - Do NOT use placeholders like [Insert Date] or [Your Phone Number] unless absolutely necessary.
    - Do NOT make up fake experiences. Stick to the provided profile.
    
    Write the cover letter now.
    """

    # Generate letter
    letter = call_ai(prompt, system_prompt="You are an expert ATS-focused Recruiter and Career Coach.")

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
    You are a Senior Technical Recruiter and Resume Expert. You have reviewed thousands of resumes and know exactly what passes ATS scanners and impresses hiring managers.

    Review the following CV data deeply.

    --- CANDIDATE CV ---
    Target Role (implied): {current_title}
    Skills Reported: {', '.join(skills)}
    Full CV Data (JSON): 
    {json.dumps(cv, indent=2)}

    --- ANALYSIS INSTRUCTIONS ---
    Provide a structured report in Markdown format with the following sections:

    ### 1. 🎯 Executive Summary
    - Brief assessment of the CV's overall impact (1-2 sentences).
    - Give a "Score" out of 10 based on content, clarity, and impact.

    ### 2. 🤖 ATS Compatibility Check
    - **Keywords**: Are the listed skills relevant for a {current_title}? What top keywords are missing?
    - **Formatting**: (Note: purely text-based analysis) Are the descriptions detailed enough?

    ### 3. 💣 Impact & Content Analysis (The most important part)
    - **Bullet Points**: specific critique. Do the experience bullet points show *results* (numbers, %, $) or just duties? 
    - Quote one weak bullet point from the CV and rewrite it to be result-oriented (STAR method).
    
    ### 4. 🛠️ Specific Improvements
    - List 3 actionable changes the candidate must make immediately to get more interviews.
    - Suggested stronger action verbs to use.

    ### 5. ⚠️ Red Flags (If any)
    - Typos, gaps, or vagueness.

    Be honest, direct, and constructive. Do not be overly polite if the CV needs work. Help them get the job.
    """

    # Generate review
    review = call_ai(prompt, system_prompt="You are a no-nonsense, expert CV Reviewer who gives high-value, actionable feedback.")

    return {
        "error": False,
        "cv_review": review
    }
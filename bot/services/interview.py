import os
from mistralai import Mistral
from bot.services.user_context import get_user_context
from bot.models import InterviewSession, InterviewResponse
from asgiref.sync import sync_to_async

# Initialize AI
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
client = Mistral(api_key=MISTRAL_API_KEY)

def ai_prompt(prompt: str) -> str:
    try:
        response = client.chat.complete(
            model="mistral-small-latest",
            messages=[
                {"role": "system", "content": "You are a helpful and concise assistant."},
                {"role": "user", "content": prompt.strip()}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ Error generating response: {str(e)}"


# ──────── Async DB wrappers ──────── #
@sync_to_async
def get_active_session(user):
    return InterviewSession.objects.filter(user=user, is_complete=False).first()

@sync_to_async
def create_session(user, job_title):
    return InterviewSession.objects.create(user=user, job_title=job_title)

@sync_to_async
def get_last_response(session):
    return InterviewResponse.objects.filter(session=session).last()

@sync_to_async
def save_response(response):
    response.save()

@sync_to_async
def count_main_answers(session):
    return InterviewResponse.objects.filter(session=session, is_follow_up=False).exclude(answer="").count()

@sync_to_async
def mark_session_complete(session):
    session.is_complete = True
    session.save()

@sync_to_async
def get_qa_pairs(session):
    return list(InterviewResponse.objects.filter(session=session).values_list("question", "answer"))

@sync_to_async
def get_all_questions(session):
    return list(InterviewResponse.objects.filter(session=session).values_list("question", flat=True))

@sync_to_async
def create_question(session, question, is_follow_up=False):
    return InterviewResponse.objects.create(
        session=session,
        question=question,
        answer="",
        is_follow_up=is_follow_up
    )

@sync_to_async
def last_question_was_follow_up(session):
    last = InterviewResponse.objects.filter(session=session).last()
    return last.is_follow_up if last else False

@sync_to_async
def cancel_session(user):
    session = InterviewSession.objects.filter(user=user, is_complete=False).first()
    if session:
        session.delete()
        return True
    return False

# ──────── Main Logic ──────── #
async def handle_interview_practice(user, user_input=None):
    session = await get_active_session(user)
    context = get_user_context(user)
    job_title = context.get("job_title") or "General Job Role"

    if not session:
        session = await create_session(user, job_title)

    if user_input:
        last_response = await get_last_response(session)
        if last_response:
            last_response.answer = user_input.strip()
            await save_response(last_response)

            # Only ask follow-up if last was a main question
            if not last_response.is_follow_up:
                follow_up_prompt = f"""
                You are a senior interviewer evaluating a candidate for the role of "{job_title}".
                
                CONTEXT:
                The candidate was asked: "{last_response.question}"
                They answered: "{last_response.answer}"

                TASK:
                Ask a probing follow-up question to test their depth of knowledge or clarify a specific part of their answer.
                Focus on "How" and "Why".
                Make it short, conversational, but challenging.
                Only return the question text.
                """
                follow_up = ai_prompt(follow_up_prompt)
                await create_question(session, follow_up, is_follow_up=True)
                return f"🔁 *Follow-Up:* {follow_up.strip()}"

    # Only main questions count toward completion
    answered_main = await count_main_answers(session)
    if answered_main >= session.total_questions:
        await mark_session_complete(session)
        qa_pairs = await get_qa_pairs(session)
        combined_qa = "\n".join([f"Q: {q}\nA: {a}" for q, a in qa_pairs])

        review_prompt = f"""
        You are an expert Interview Coach. Review this completed mock interview for the role of '{job_title}'.

        TRANSCRIPT:
        {combined_qa}

        TASK:
        Provide a comprehensive performance review.
        
        Output Format (Markdown):
        ### 🏆 Overall Verdict
        (Pass/Fail/Borderline) with a 1-sentence summary.

        ### ✅ Strengths
        - Bullet points of what they did well (examples: clarity, STAR method usage, technical depth).

        ### ⚠️ Areas for Improvement
        - Bullet points of specific weak answers and why they were weak.
        - "Did they answer the question asked?"
        - "Did they use the STAR method (Situation, Task, Action, Result)?"

        ### 💡 Key Advice
        - One actionable tip for their next real interview.
        """
        review = ai_prompt(review_prompt)
        return f"✅ **Mock Interview Complete!**\n\n{review}"

    # Generate a new unique main question
    past_questions = await get_all_questions(session)
    question_list_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(past_questions)]) or "None yet."

    main_prompt = f"""
    You are a Hiring Manager for the role of "{job_title}".
    
    GOAL: Conduct a rigorous interview.
    
    HISTORY (Already Asked):
    {question_list_text}

    TASK:
    Generate question #{answered_main + 1} of {session.total_questions}.
    
    CRITERIA:
    - If this is question 1, ask a "Tell me about yourself" or background question relevant to {job_title}.
    - If mid-interview, ask a behavioral ("Tell me about a time...") or situational ("How would you handle...") question.
    - If last question, ask a big-picture contribution question.
    
    Ensure the question is unique from the history. 
    Only return the question text.
    """
    question = ai_prompt(main_prompt)
    await create_question(session, question, is_follow_up=False)

    return f"🎤 *Question {answered_main + 1} of {session.total_questions}:*\n\n{question.strip()}"
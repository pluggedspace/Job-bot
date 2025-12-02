import os
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
from bot.services.user_context import get_user_context
from bot.models import InterviewSession, InterviewResponse
from asgiref.sync import sync_to_async

# Initialize AI
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
client = MistralClient(api_key=MISTRAL_API_KEY)

def ai_prompt(prompt: str) -> str:
    try:
        response = client.chat(
            model="mistral-small",
            messages=[
                ChatMessage(role="system", content="You are a helpful and concise assistant."),
                ChatMessage(role="user", content=prompt.strip())
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
                You're a smart interviewer conducting a mock interview for the role of "{job_title}".

                The candidate was asked:
                Q: {last_response.question}

                They answered:
                A: {last_response.answer}

                Now ask a relevant follow-up question to dig deeper into their answer.
                Make it short, clear, and insightful. Only return the follow-up question.
                """
                follow_up = ai_prompt(follow_up_prompt)
                await create_question(session, follow_up, is_follow_up=True)
                return f"🔁 *Follow-Up Question:*\n\n{follow_up.strip()}"

    # Only main questions count toward completion
    answered_main = await count_main_answers(session)
    if answered_main >= session.total_questions:
        await mark_session_complete(session)
        qa_pairs = await get_qa_pairs(session)
        combined_qa = "\n".join([f"Q: {q}\nA: {a}" for q, a in qa_pairs])

        review_prompt = f"""
        You're an interview coach. Review this mock interview for the role of '{job_title}'.

        {combined_qa}

        Give a summary of the candidate's performance including:
        - Strengths
        - Weaknesses
        - Suggestions to improve
        """
        review = ai_prompt(review_prompt)
        return f"✅ **Mock Interview Complete!**\n\n📝 *Your Review:*\n\n{review}"

    # Generate a new unique main question
    past_questions = await get_all_questions(session)
    question_list_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(past_questions)]) or "None yet."

    main_prompt = f"""
    You're a professional interviewer for the role of "{job_title}".

    These are the questions already asked:
    {question_list_text}

    Ask a new, unique, and insightful interview question (question {answered_main + 1} of {session.total_questions}).
    Do NOT repeat topics. Only return the question.
    """
    question = ai_prompt(main_prompt)
    await create_question(session, question, is_follow_up=False)

    return f"🎤 *Question {answered_main + 1} of {session.total_questions}:*\n\n{question.strip()}"
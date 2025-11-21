import os
import json
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage

# Replace this function to use Mixtral instead of Gemini
def query_mixtral_for_upskill_path(role):
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        print("❌ No MISTRAL_API_KEY found.")
        return None

    try:
        client = MistralClient(api_key=api_key)
        model = "mistral-small-latest"

        prompt = (
            f"You are a career coach AI.\n"
            f"Suggest the top 5 skills needed to become a {role}.\n"
            f"For each skill, include 1 free course recommendation with the course title and URL.\n"
            f"Return the result as **valid JSON only** in this format:\n"
            f"{{\n"
            f"  \"skills\": [\n"
            f"    {{\"name\": \"Skill Name\", \"course\": {{\"title\": \"Course Title\", \"url\": \"https://...\"}} }},\n"
            f"    ... (5 total)\n"
            f"  ]\n"
            f"}}"
        )

        messages = [ChatMessage(role="user", content=prompt)]
        response = client.chat(model=model, messages=messages)

        # Extract and parse JSON from the response
        text = response.choices[0].message.content.strip()
        text = text.strip("```json").strip("```").strip()
        return json.loads(text)

    except Exception as e:
        print("❌ Mixtral JSON parsing failed:", e)

    return None


def get_upskill_plan(user, user_input=None):
    print("🔥 Mixtral upskill plan running for:", user_input)
    if not user_input:
        return {
            "target": None,
            "skills_to_gain": [],
            "resources": [],
            "note": "Please provide a job role to upskill for."
        }

    ai_result = query_mixtral_for_upskill_path(user_input)
    if ai_result and ai_result.get("skills"):
        return {
            "target": user_input.title(),
            "skills_to_gain": ai_result["skills"],
            "resources": [skill["course"] for skill in ai_result["skills"]],
            "note": "Generated using Mixtral AI."
        }

    return {
        "target": user_input.title(),
        "skills_to_gain": [],
        "resources": [],
        "note": "Failed to generate upskill plan. Please try again or check API key."
    }
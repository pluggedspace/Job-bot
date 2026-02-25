import os
import json
from mistralai import Mistral

# Replace this function to use AI
def query_ai_for_upskill_path(role):
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        print("❌ No MISTRAL_API_KEY found.")
        return None

    try:
        client = Mistral(api_key=api_key)
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

        messages = [{"role": "user", "content": prompt}]
        response = client.chat.complete(model=model, messages=messages)

        # Extract and parse JSON from the response
        text = response.choices[0].message.content.strip()
        # Handle potential markdown code blocks
        if "```" in text:
            text = text.split("```json")[-1].split("```")[0].strip()
        elif "```" in text: # fallback if json tag missing
            text = text.split("```")[-1].split("```")[0].strip()
            
        return json.loads(text)

    except Exception as e:
        print(f"❌ AI Error: {str(e)}")
        # Return a partial result with error info if possible, or just None
        return None


def get_upskill_plan(user, user_input=None):
    print("🔥 Upskill plan running for:", user_input)
    if not user_input:
        return {
            "target": None,
            "skills_to_gain": [],
            "resources": [],
            "note": "Please provide a job role to upskill for."
        }

    ai_result = query_ai_for_upskill_path(user_input)
    if ai_result and ai_result.get("skills"):
        return {
            "target": user_input.title(),
            "skills_to_gain": ai_result["skills"],
            "resources": [skill["course"] for skill in ai_result["skills"]],
            "note": ""
        }

    return {
        "target": user_input.title(),
        "skills_to_gain": [],
        "resources": [],
        "note": "Failed to generate upskill plan. Please try again or check API key."
    }
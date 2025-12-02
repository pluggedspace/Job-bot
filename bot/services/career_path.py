import os
import json
import requests
from django.utils.text import slugify
from .user_context import get_user_context
from bot.models import CareerPathCache
from urllib.parse import quote
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage


def resolve_career_path(job_title: str):
    # 1. Try AI
    ai_data = fetch_career_path_ai(job_title)
    if ai_data and any([ai_data.get("broader"), ai_data.get("narrower"), ai_data.get("related")]):
        ai_data["input_title"] = job_title
        return ai_data, 'AI'

    # 2. Fallback to ONET
    onet_data = fetch_career_path_onet(job_title)
    if onet_data:
        onet_data["input_title"] = job_title
        return onet_data, 'ONET'

    # 3. Fallback to local JSON
    fallback = fetch_career_path_fallback(job_title)
    if fallback:
        fallback["input_title"] = job_title
        return fallback, 'Fallback'

    return {"error": "No career path data available.", "input_title": job_title}, None


def fetch_career_path_ai(job_title):
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        print("❌ No MISTRAL_API_KEY found.")
        return None

    try:
        client = MistralClient(api_key=api_key)
        model = "mistral-small-latest"

        prompt = (
            f"You are a career taxonomy assistant.\n"
            f"Given the job title '{job_title}', return related roles as JSON in the following format:\n"
            f"{{\n"
            f"  \"broader\": [\"...\"],\n"
            f"  \"narrower\": [\"...\"],\n"
            f"  \"related\": [\"...\"]\n"
            f"}}\n"
            f"Only return valid JSON. No explanation. Avoid markdown fencing."
        )

        messages = [ChatMessage(role="user", content=prompt)]
        response = client.chat(model=model, messages=messages)

        content = response.choices[0].message.content.strip()
        content = content.strip("```json").strip("```").strip()
        return json.loads(content)

    except Exception as e:
        print("❌ AI career path error:", e)
        return None


def fetch_career_path_onet(job_title):
    api_key = "am9iX3BsdWdnZWRzcGFjZV9vcmc6ODg5NnFycw=="
    search_url = f"https://services.onetcenter.org/ws/online/occupations?keyword={quote(job_title)}"
    headers = {"Authorization": f"Basic {api_key}"}

    resp = requests.get(search_url, headers=headers)
    if not resp.ok:
        return None

    occupations = resp.json().get('occupation', [])
    if not occupations:
        return None

    occ_code = occupations[0].get('code')
    title = occupations[0].get('title')

    related_url = f"https://services.onetcenter.org/ws/online/occupations/{occ_code}/related"
    rel_resp = requests.get(related_url, headers=headers)
    related = [r['title'] for r in rel_resp.json().get('related_occupation', [])] if rel_resp.ok else []

    return {
        "input_title": job_title,
        "onet_code": occ_code,
        "broader": [],
        "narrower": [],
        "related": related
    }


def fetch_career_path_fallback(job_title):
    with open("fallback_career_paths.json") as f:
        data = json.load(f)
    return data.get(job_title)


def get_career_path_data(user, input_title=None):
    context = get_user_context(user, input_title)
    job_title = context['job_title']
    if not job_title:
        return None

    normalized = slugify(job_title)
    cached = CareerPathCache.objects.filter(normalized_title=normalized).first()
    if cached:
        return cached.result_data

    path_data, source = resolve_career_path(job_title)
    if not path_data:
        return None

    CareerPathCache.objects.create(
        input_title=job_title,
        normalized_title=normalized,
        result_data=path_data
    )
    return path_data
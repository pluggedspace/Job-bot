import requests
import logging
from django.conf import settings
import datetime

logger = logging.getLogger(__name__)

# Paystack Utils
def create_paystack_payment(email: str, amount: int, reference: str = None) -> dict:
    url = "https://api.paystack.co/transaction/initialize"
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "email": email,
        "amount": amount * 100,
        "callback_url": "https://yourdomain.com/callback/"
    }
    if reference:
        data["trxref"] = reference
    try:
        response = requests.post(url, headers=headers, json=data, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Paystack error: {e}")
        return {"status": False, "message": str(e)}

def verify_paystack_payment(reference: str) -> dict:
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Verification error: {e}")
        return {"status": False, "message": str(e)}

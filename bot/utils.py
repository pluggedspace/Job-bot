import requests
import logging
from django.conf import settings
import datetime
import time

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
        data["reference"] = reference
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


# Flutterwave Utils
def create_flutterwave_payment(email: str, amount: float, currency: str = "USD", reference: str = None) -> dict:
    """
    Create Flutterwave payment link
    Args:
        email: Customer email
        amount: Amount in the specified currency (e.g., 9.99 for USD)
        currency: Currency code (USD, NGN, EUR, GBP, etc.)
        reference: Optional payment reference
    """
    url = "https://api.flutterwave.com/v3/payments"
    headers = {
        "Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    
    if not reference:
        reference = f"FLW_{int(time.time())}"
    
    data = {
        "tx_ref": reference,
        "amount": str(amount),
        "currency": currency,
        "redirect_url": "https://api.pluggedspace.org/job/api/flutterwave/callback/",
        "customer": {
            "email": email
        },
        "customizations": {
            "title": "Job Autobot Premium Subscription",
            "description": "Monthly Premium Subscription",
            "logo": "https://pluggedspace.org/assets/pluggedspaceicon.png"
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Flutterwave error: {e}")
        return {"status": "error", "message": str(e)}

def verify_flutterwave_payment(transaction_id: str) -> dict:
    """Verify Flutterwave payment"""
    url = f"https://api.flutterwave.com/v3/transactions/{transaction_id}/verify"
    headers = {
        "Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Flutterwave verification error: {e}")
        return {"status": "error", "message": str(e)}

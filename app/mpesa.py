"""
M-Pesa Daraja API integration (sandbox).

Handles:
- OAuth access token retrieval
- STK Push (Lipa Na M-Pesa) initiation
- Callback verification helper

Docs: https://developer.safaricom.co.ke/Documentation
"""
import os
import base64
import requests
from datetime import datetime

DARAJA_BASE_URL = "https://sandbox.safaricom.co.ke"


def get_access_token():
    """Fetch a short-lived OAuth access token from Daraja."""
    consumer_key = os.environ["MPESA_CONSUMER_KEY"]
    consumer_secret = os.environ["MPESA_CONSUMER_SECRET"]

    url = f"{DARAJA_BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
    response = requests.get(url, auth=(consumer_key, consumer_secret), timeout=10)
    response.raise_for_status()
    return response.json()["access_token"]


def _generate_password(shortcode, passkey, timestamp):
    raw = f"{shortcode}{passkey}{timestamp}"
    return base64.b64encode(raw.encode()).decode()


def normalize_phone(phone):
    """
    Convert common Kenyan phone formats to Daraja's required 2547XXXXXXXX format.
    Accepts: 07XXXXXXXX, 7XXXXXXXX, 2547XXXXXXXX, +2547XXXXXXXX
    """
    phone = phone.strip().replace(" ", "").replace("-", "")
    if phone.startswith("+"):
        phone = phone[1:]
    if phone.startswith("0"):
        phone = "254" + phone[1:]
    if phone.startswith("7") and len(phone) == 9:
        phone = "254" + phone
    return phone


def stk_push(phone, amount, account_reference, transaction_desc):
    """
    Trigger an STK Push (Lipa Na M-Pesa Online) prompt on the customer's phone.

    Returns the raw Daraja response dict, which includes:
    - MerchantRequestID
    - CheckoutRequestID (needed to query status later)
    - ResponseCode ("0" means the push was sent successfully)
    """
    shortcode = os.environ["MPESA_SHORTCODE"]
    passkey = os.environ["MPESA_PASSKEY"]
    callback_url = os.environ["MPESA_CALLBACK_URL"]

    access_token = get_access_token()
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    password = _generate_password(shortcode, passkey, timestamp)

    payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(round(amount)),  # Daraja sandbox requires a whole number
        "PartyA": normalize_phone(phone),
        "PartyB": shortcode,
        "PhoneNumber": normalize_phone(phone),
        "CallBackURL": callback_url,
        "AccountReference": account_reference[:12],  # Daraja limits this field
        "TransactionDesc": transaction_desc[:13],
    }

    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"{DARAJA_BASE_URL}/mpesa/stkpush/v1/processrequest"

    response = requests.post(url, json=payload, headers=headers, timeout=15)
    if not response.ok:
        raise Exception(f"Daraja error {response.status_code}: {response.text}")
    return response.json()

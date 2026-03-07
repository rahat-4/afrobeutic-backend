import logging
import requests
from django.conf import settings
from twilio.rest import Client
from .crypto import decrypt_data

logger = logging.getLogger(__name__)

GRAPH_API_VERSION = "v19.0"
GRAPH_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


# ─────────────────────────────────────────────────────────────────────────────
# 1. Exchange short-lived code → long-lived access token
# ─────────────────────────────────────────────────────────────────────────────


def exchange_code_for_token(code: str) -> str:
    """
    Exchange the short-lived OAuth code Meta sends to the frontend
    for a long-lived System User access token.

    Requires in settings:
      META_APP_ID       — your Meta App ID
      META_APP_SECRET   — your Meta App Secret

    Returns the access_token string.
    Raises on failure.
    """
    url = f"{GRAPH_BASE}/oauth/access_token"
    params = {
        "client_id": settings.META_APP_ID,
        "client_secret": settings.META_APP_SECRET,
        "code": code,
        # No redirect_uri needed for server-side exchange
    }

    response = requests.get(url, params=params, timeout=10)

    if response.status_code != 200:
        logger.error(
            "Meta token exchange failed (%s): %s",
            response.status_code,
            response.text,
        )
        raise Exception(
            f"Meta token exchange failed: {response.status_code} — {response.text}"
        )

    data = response.json()
    access_token = data.get("access_token")
    if not access_token:
        raise Exception(f"No access_token in Meta response: {data}")

    logger.info("Successfully exchanged Meta code for access token")
    return access_token


# ─────────────────────────────────────────────────────────────────────────────
# 2. Fetch actual phone number using phone_number_id
# ─────────────────────────────────────────────────────────────────────────────


def fetch_whatsapp_number(phone_number_id: str, access_token: str) -> str:
    """
    Fetch the actual E.164 phone number for a given phone_number_id
    from the Meta Graph API.

    Returns the number as a string WITHOUT the leading +, e.g. "15551234567"
    Raises on failure.
    """
    url = f"{GRAPH_BASE}/{phone_number_id}"
    params = {
        "fields": "display_phone_number,verified_name,code_verification_status",
        "access_token": access_token,
    }

    response = requests.get(url, params=params, timeout=10)

    if response.status_code != 200:
        logger.error(
            "Meta phone number fetch failed (%s): %s",
            response.status_code,
            response.text,
        )
        raise Exception(
            f"Meta phone number fetch failed: {response.status_code} — {response.text}"
        )

    data = response.json()
    # Meta returns display_phone_number like "+1 555 123 4567"
    raw = data.get("display_phone_number", "")
    if not raw:
        raise Exception(f"No display_phone_number in Meta response: {data}")

    # Normalise to E.164 digits only, then re-add + in the caller
    normalised = "+" + "".join(filter(str.isdigit, raw))
    logger.info(
        "Fetched WhatsApp number %s for phone_number_id %s", normalised, phone_number_id
    )
    return normalised


def sync_sender_status(chatbot_config):
    account_sid = decrypt_data(chatbot_config.account_sid, settings.CRYPTO_PASSWORD)
    auth_token = decrypt_data(chatbot_config.auth_token, settings.CRYPTO_PASSWORD)
    sender_sid = chatbot_config.sender_sid

    client = Client(account_sid, auth_token)

    sender = client.messaging.v2.channels_senders(sender_sid).fetch()

    chatbot_config.status = sender.status
    chatbot_config.save(update_fields=["status"])

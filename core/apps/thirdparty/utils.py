import logging
from django.conf import settings
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

logger = logging.getLogger(__name__)

INBOUND_WEBHOOK_URL = "https://api.afrobeutic.com/api/whatsapp-callback/"


def get_whatsapp_senders(account_sid: str, auth_token: str) -> list:
    """
    Returns a list of WhatsApp-enabled phone numbers for the given Twilio account.
    """
    client = Client(account_sid, auth_token)
    try:
        numbers = client.incoming_phone_numbers.list()
    except TwilioRestException as e:
        logger.error("Failed to fetch numbers for account %s: %s", account_sid, str(e))
        return []

    return [n.phone_number for n in numbers]


def get_or_create_subaccount(friendly_name: str) -> dict:
    """
    Returns a subaccount with <3 WhatsApp senders, or creates a new one.
    """
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    try:
        subaccounts = client.api.v2010.accounts.list()
    except TwilioRestException as e:
        logger.error("Failed to list subaccounts: %s", str(e))
        subaccounts = []

    for sub in subaccounts:
        if sub.sid == settings.TWILIO_ACCOUNT_SID:
            continue

        whatsapp_numbers = get_whatsapp_senders(sub.sid, sub.auth_token)
        if len(whatsapp_numbers) < 3:
            logger.info(
                "Using existing subaccount %s (%s) with %d WhatsApp numbers",
                sub.sid,
                friendly_name,
                len(whatsapp_numbers),
            )
            return {"account_sid": sub.sid, "auth_token": sub.auth_token}

    # Create new subaccount
    new_account = client.api.v2010.accounts.create(friendly_name=friendly_name)
    logger.info(
        "Created new subaccount %s for WABA %s (%s)",
        new_account.sid,
        friendly_name,
    )
    return {"account_sid": new_account.sid, "auth_token": new_account.auth_token}

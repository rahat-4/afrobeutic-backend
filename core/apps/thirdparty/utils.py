from twilio.rest import Client

from django.conf import settings


def create_twilio_subaccount(friendly_name):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    subaccount = client.api.v2010.accounts.create(friendly_name=friendly_name)
    return {
        "account_sid": subaccount.sid,
        "auth_token": subaccount.auth_token,
    }

def register_twilio_whatsapp_sender(subaccount_sid, subaccount_auth_token, waba_id, phone_number):
    client = Client(subaccount_sid, subaccount_auth_token)
    sender = client.messaging.v2.channels.senders.create(
        sender_id=f"whatsapp:{phone_number}",
        configuration={"waba_id": waba_id},
        profile={"address": "My Business", "vertical": "Other"},
    )
    return {
        "sid": sender.sid,
        "status": sender.status,
    }
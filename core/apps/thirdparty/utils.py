import json

from twilio.rest import Client
from twilio.rest.messaging.v2 import ChannelsSenderList

from django.conf import settings


def create_twilio_subaccount(friendly_name):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    subaccount = client.api.v2010.accounts.create(friendly_name=friendly_name)
    return {
        "account_sid": subaccount.sid,
        "auth_token": subaccount.auth_token,
    }


def check_phone_number_status(
    subaccount_sid: str,
    subaccount_auth_token: str,
):
    from twilio.rest import Client

    client = Client(subaccount_sid, subaccount_auth_token)

    # Check incoming phone numbers
    numbers = client.incoming_phone_numbers.list()

    print("Available phone numbers:")
    for number in numbers:
        print(f"  {number.phone_number} - {number.friendly_name}")

    return numbers


# def create_whatsapp_sender(
#     subaccount_sid: str,
#     subaccount_auth_token: str,
#     waba_id: str,
#     phone_number_id: str,
#     phone_number: str,
# ):
#     import requests
#     from requests.auth import HTTPBasicAuth


#     # Test 1: Verify authentication works by listing existing senders
#     print("Testing authentication...")
#     list_response = requests.get(
#         "https://messaging.twilio.com/v2/Channels/Senders",
#         auth=HTTPBasicAuth(subaccount_sid, subaccount_auth_token),
#     )
#     print(f"List senders status: {list_response.status_code}")
#     print(f"List senders response: {list_response.text}")

#     # Test 2: Try creating with minimal payload
#     print("\nAttempting to create sender...")
#     payload = {
#         "sender_type": "whatsapp",
#         "sender_id": f"whatsapp:15557808321",  # Without +
#         "configuration": {
#             "provider": "whatsapp",
#             "waba_id": str(waba_id),  # Ensure it's a string
#             "phone_number_id": str(phone_number_id),  # Ensure it's a string
#         },
#     }

#     print(f"Payload: {json.dumps(payload, indent=2)}")

#     response = requests.post(
#         "https://messaging.twilio.com/v2/Channels/Senders",
#         auth=HTTPBasicAuth(subaccount_sid, subaccount_auth_token),
#         headers={"Content-Type": "application/json"},
#         json=payload,
#     )

#     print(f"Create status: {response.status_code}")
#     print(f"Create response: {response.text}")

#     return response.json() if response.status_code == 201 else None


def create_whatsapp_sender(
    subaccount_sid: str,
    subaccount_auth_token: str,
    waba_id: str,
    phone_number: str,
    phone_number_id: str,
):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    test = check_phone_number_status(
        settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN
    )
    print("lllllllllllllllllllllllllllllllll", test)
    payload = {
        "sender_id": f"whatsapp:+{phone_number_id}",
        "configuration": {
            "waba_id": waba_id,
            # "phone_number_id": phone_number_id,
        },
        "profile": {
            "name": "Twilio",
        },
        # "webhook": {
        #     "callback_url": "https://api.afrobeutic.com/api/webhooks/whatsapp-status",
        #     "callback_method": "POST",
        # },
    }

    response = client.request(
        method="POST",
        uri="https://messaging.twilio.com/v2/Channels/Senders",
        data=payload,
        headers={"Content-Type": "application/json"},
    )

    print(f"Twilio API response status: {response.status_code}")
    print(f"Twilio API response content: {response.content}")
    content = response.content.decode("utf-8") if response.content else "{}"
    return json.loads(content)


# def create_whatsapp_sender(
#     subaccount_sid, subaccount_auth_token, waba_id, phone_number
# ):
#     client = Client(subaccount_sid, subaccount_auth_token)
#     payload = {
#         "sender_id": f"whatsapp:{phone_number}",
#         "profile": {
#             "name": "My Business Display Name"  # required for WhatsApp sender registration
#         },
#         "configuration": {"waba_id": waba_id},
#         "webhook": {
#             "callback_url": "https://api.afrobeutic.com/webhooks/whatsapp-chat",
#             "callback_method": "POST",
#         },
#     }

#     response = client.request(
#         "POST",
#         "https://messaging.twilio.com/v2/Channels/Senders",
#         data=json.dumps(payload),
#         headers={"Content-Type": "application/json"},
#     )

# response = client.messaging.v2.channels_senders.create(
#     messaging_v2_channels_sender_requests_create=ChannelsSenderList.MessagingV2ChannelsSenderRequestsCreate(
#         {
#             "sender_id": f"whatsapp:{phone_number}",
#             "configuration": {"waba_id": waba_id},
#         }
#     )
# )


def configure_subaccount(subaccount_sid: str, subaccount_auth_token: str) -> None:
    print(f"Configuring subaccount {subaccount_sid} with provided auth token")
    client = Client(subaccount_sid, subaccount_auth_token)
    # Example: Set the subaccount's status to active
    client.api.accounts(subaccount_sid).update(
        sms_url="https://api.afrobeutic.com/webhooks/whatsapp-chat",
        status_callback="https://api.afrobeutic.com/webhooks/whatsapp-status",
    )

    print(f"Subaccount {subaccount_sid} configured successfully")

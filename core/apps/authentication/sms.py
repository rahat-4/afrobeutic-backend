from twilio.rest import Client
from django.conf import settings


def send_otp_sms(phone_number, otp):
    client = Client(
        settings.TWILIO_ACCOUNT_SID,
        settings.TWILIO_AUTH_TOKEN,
    )

    message = client.messages.create(
        body=f"Your OTP code is {otp}. It will expire in 5 minutes.",
        from_=settings.TWILIO_SMS_FROM,
        to=phone_number,
    )

    return message.sid


def send_otp_whatsapp(phone_number, otp):
    client = Client(
        settings.TWILIO_ACCOUNT_SID,
        settings.TWILIO_AUTH_TOKEN,
    )

    print("Sending WhatsApp OTP", phone_number, otp)

    message = client.messages.create(
        body=f"🔐 Your OTP is *{otp}*. It expires in 5 minutes.",
        from_=settings.TWILIO_WHATSAPP_FROM,
        to=f"whatsapp:{phone_number}",
    )

    print("Twilio response:", message.sid, message.status)

    return message.sid

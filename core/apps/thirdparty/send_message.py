import logging

from twilio.rest import Client

logger = logging.getLogger(__name__)


def send_whatsapp_reply(
    twilio_sid: str, twilio_token: str, to: str, from_: str, body: str
) -> None:
    """Send a WhatsApp message via Twilio."""
    try:
        twilio = Client(twilio_sid, twilio_token)
        twilio.messages.create(
            body=body,
            from_=from_,
            to=to,
        )
    except Exception as exc:
        logger.error("Failed to send WhatsApp reply to %s: %s", to, exc)

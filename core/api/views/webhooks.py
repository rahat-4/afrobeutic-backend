import logging
import stripe
from decouple import config
from twilio.rest import Client as TwilioClient

from django.conf import settings
from django.core.mail import send_mail
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.billing.utils import handle_payment_failed, handle_payment_success
from apps.salon.models import Customer
from apps.thirdparty.models import (
    MetaConfig,
    WhatsappChatbotConfig,
    WhatsappChatbotMessageLog,
)
from apps.thirdparty.send_message import send_whatsapp_reply
from apps.thirdparty.choices import WhatsappChatbotMessageRole

from common.choices import CategoryType
from common.utils import get_or_create_category
from common.crypto import decrypt_data, encrypt_data


logger = logging.getLogger(__name__)


def _crypto_password() -> str:
    return config("CRYPTO_PASSWORD")


def _encrypt(value: str) -> dict:
    return encrypt_data(value, _crypto_password())


def _decrypt(blob: dict) -> str:
    return decrypt_data(blob, _crypto_password())


def _log_message(
    bot: WhatsappChatbotConfig,
    customer: Customer,
    message: str,
    role: str,
) -> None:
    try:
        WhatsappChatbotMessageLog.objects.create(
            chatbot=bot,
            customer=customer,
            message=message,
            role=role,
        )
    except Exception as exc:
        logger.warning("Could not save message log: %s", exc)


def _send_whatsapp_reply(
    account_sid: str,
    auth_token: str,
    to: str,
    from_: str,
    body: str,
) -> None:
    try:
        client = TwilioClient(account_sid, auth_token)
        client.messages.create(body=body, from_=from_, to=to)
    except Exception as exc:
        logger.error("Failed to send WhatsApp reply to %s: %s", to, exc)


@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def stripe_webhook(request):
    print(
        "======================================== Stripe Webhook Received ============================="
    )
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET,
        )
        print(f"Event verified successfully: {event['type']}")
    except ValueError as e:
        print(f"Invalid payload: {e}")
        return Response(status=400)
    except stripe.error.SignatureVerificationError as e:
        print(f"Invalid signature: {e}")
        return Response(status=400)

    event_type = event["type"]
    payment_intent = event["data"]["object"]

    if event_type == "payment_intent.succeeded":
        handle_payment_success(payment_intent)
        print(
            "================================ Payment Intent Succeeded ================================"
        )
    elif event_type == "payment_intent.payment_failed":
        handle_payment_failed(payment_intent)
        print(
            "================================ Payment Intent Failed ================================"
        )

    return Response(status=200)


@method_decorator(csrf_exempt, name="dispatch")
class WhatsappCallbackView(APIView):
    """
    Receives inbound WhatsApp messages from Twilio.

    Routing:  Twilio sends To=whatsapp:+SALON_NUMBER.
              We look up MetaConfig by whatsapp_number → find the salon
              → find its chatbot config.

    Replies go out through the salon's own Twilio subaccount credentials
    (stored encrypted in MetaConfig), NOT the master account.
    """

    permission_classes = []

    def post(self, request, *args, **kwargs):
        # ── 1. Parse Twilio payload ───────────────────────────────────────────
        profile_name = request.data.get("ProfileName", "").strip()
        from_number = request.data.get("From", "").strip()  # customer's WA number
        incoming_message = request.data.get("Body", "").strip()
        to_number = request.data.get("To", "").strip()  # salon's WA number

        print("------------------------------------------------>", incoming_message)

        if not all([from_number, incoming_message, to_number]):
            logger.warning(
                "WhatsApp callback missing required fields: %s", request.data
            )
            return JsonResponse(
                {"status": "error", "message": "Missing required fields"},
                status=400,
            )

        # ── 2. Route to salon via MetaConfig ──────────────────────────────────
        # Strip "whatsapp:" prefix Twilio adds to the To field
        salon_number = to_number.replace("whatsapp:", "").strip()

        try:
            meta = MetaConfig.objects.select_related("salon", "account").get(
                whatsapp_number=salon_number
            )
        except MetaConfig.DoesNotExist:
            logger.error("No MetaConfig found for number: %s", salon_number)
            return JsonResponse(
                {"status": "error", "message": "Salon not found for this number"},
                status=404,
            )

        salon = meta.salon
        account = meta.account

        # ── 3. Resolve chatbot config ─────────────────────────────────────────
        bot = getattr(salon, "whatsapp_chatbot_config", None)
        if not bot or not bot.is_active:
            logger.warning("Chatbot inactive or missing for salon: %s", salon.name)
            return JsonResponse({"status": "ok"})

        # ── 4. Resolve or create customer ─────────────────────────────────────
        customer_phone = from_number.replace("whatsapp:", "").strip()
        name_parts = profile_name.split(maxsplit=1)
        first_name = name_parts[0] if name_parts else customer_phone
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        source = get_or_create_category(
            "Whatsapp", account, category_type=CategoryType.CUSTOMER_SOURCE
        )
        customer, _ = Customer.objects.get_or_create(
            phone=customer_phone,
            defaults={
                "first_name": first_name,
                "last_name": last_name,
                "source": source,
                "account": account,
                "salon": salon,
            },
        )

        # ── 5. Log inbound message ────────────────────────────────────────────
        _log_message(
            bot, customer, incoming_message, WhatsappChatbotMessageRole.CUSTOMER
        )

        # ── 6. Check message quota ────────────────────────────────────────────
        if not bot.has_remaining_messages():
            logger.warning("Message limit reached for salon: %s", salon.name)
            # Silently drop — customer already got a reply from their last message
            return JsonResponse({"status": "ok"})

        # ── 7. Run OpenAI assistant ───────────────────────────────────────────
        try:
            from openAI.assistant_service import run_assistant

            reply = run_assistant(
                salon=salon,
                customer=customer,
                user_message=incoming_message,
            )
        except Exception as exc:
            logger.exception("Assistant run failed for %s: %s", customer_phone, exc)
            reply = (
                "Sorry, we're experiencing a technical issue. "
                "Please try again or call us directly."
            )

        # ── 8. Log outbound reply ─────────────────────────────────────────────
        _log_message(bot, customer, reply, WhatsappChatbotMessageRole.ASSISTANT)

        # ── 9. Send reply using salon's own Twilio subaccount ─────────────────
        _send_whatsapp_reply(
            account_sid=_decrypt(meta.account_sid),
            auth_token=_decrypt(meta.auth_token),
            to=from_number,  # back to the customer
            from_=to_number,  # from the salon's number
            body=reply,
        )

        return Response({"status": "ok"})


@method_decorator(csrf_exempt, name="dispatch")
class WhatsappStatusCallbackView(APIView):
    permission_classes = []

    def post(self, request, *args, **kwargs):
        # print("request=================================>", request.data)
        return Response({"status": "ok"})


@method_decorator(csrf_exempt, name="dispatch")
class WhatsappFallbackView(APIView):
    permission_classes = []

    def post(self, request, *args, **kwargs):
        print("request=================================>", request.data)
        return Response({"status": "ok"})

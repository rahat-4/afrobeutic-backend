import logging
import stripe
from decouple import config
from django.conf import settings
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
from apps.thirdparty.models import WhatsappChatbotConfig, WhatsappChatbotMessageLog
from apps.thirdparty.send_message import send_whatsapp_reply
from apps.thirdparty.choices import WhatsappChatbotMessageRole

from common.choices import CategoryType
from common.utils import get_or_create_category
from common.crypto import decrypt_data


logger = logging.getLogger(__name__)


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
    permission_classes = []

    def _log_message(
        self,
        bot: WhatsappChatbotConfig,
        customer: Customer,
        message: str,
        role: str,
    ) -> None:
        """Persist a message to the log table (fire-and-forget style)."""
        try:
            WhatsappChatbotMessageLog.objects.create(
                chatbot=bot,
                customer=customer,
                message=message,
                role=role,
            )
        except Exception as exc:
            logger.warning("Could not save message log: %s", exc)

    def post(self, request, *args, **kwargs):
        # ── 1. Parse incoming Twilio payload ─────────────────────────────────
        profile_name = request.data.get("ProfileName", "").strip()
        whatsapp_number = request.data.get("From", "").strip()
        incoming_message = request.data.get("Body", "").strip()
        whatsapp_sender_number = request.data.get("To", "").strip()

        if not all([whatsapp_number, incoming_message, whatsapp_sender_number]):
            logger.warning(
                "WhatsApp callback missing required fields: %s", request.data
            )
            return JsonResponse(
                {"status": "error", "message": "Missing required fields"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── 2. Resolve chatbot config ─────────────────────────────────────────
        bot = (
            WhatsappChatbotConfig.objects.filter(
                whatsapp_sender_number=whatsapp_sender_number
            )
            .select_related("salon", "account")
            .first()
        )

        if not bot:
            logger.error(
                "No chatbot config found for number: %s", whatsapp_sender_number
            )
            return JsonResponse(
                {"status": "error", "message": "Chatbot configuration not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # ── 3. Resolve customer ───────────────────────────────────────────────
        account = bot.account
        salon = bot.salon
        phone = whatsapp_number.replace("whatsapp:", "").strip()

        name_parts = profile_name.split(maxsplit=1)
        first_name = name_parts[0] if name_parts else phone
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        source = get_or_create_category(
            "Whatsapp", account, category_type=CategoryType.CUSTOMER_SOURCE
        )

        customer, _ = Customer.objects.get_or_create(
            phone=phone,
            defaults={
                "first_name": first_name,
                "last_name": last_name,
                "source": source,
                "account": account,
                "salon": salon,
            },
        )

        # ── 4. Log incoming message ───────────────────────────────────────────
        self._log_message(
            bot, customer, incoming_message, WhatsappChatbotMessageRole.CUSTOMER
        )

        # ── 5. Run the OpenAI assistant ───────────────────────────────────────
        try:
            from openAI.assistant_service import run_assistant

            reply = run_assistant(
                salon=salon,
                customer=customer,
                user_message=incoming_message,
            )
        except Exception as exc:
            logger.exception("Assistant run failed for customer %s: %s", phone, exc)
            reply = (
                "Sorry, we're experiencing a technical issue. "
                "Please try again or call us directly."
            )

        # ── 6. Log outbound reply ─────────────────────────────────────────────
        self._log_message(bot, customer, reply, WhatsappChatbotMessageRole.BOT)

        # ── 7. Send reply via Twilio ──────────────────────────────────────────
        # Get twilio sid and auth token
        # try:
        #     crypto_password = config("CRYPTO_PASSWORD")
        #     twilio_sid = decrypt_data(
        #         account.account_meta_config.account_sid, crypto_password
        #     )
        #     twilio_token = decrypt_data(
        #         account.account_meta_config.auth_token, crypto_password
        #     )
        # except Exception as exc:
        #     logger.error(
        #         "Failed to decrypt Twilio credentials for account %s: %s",
        #         account.name,
        #         exc,
        #     )
        #     return JsonResponse(
        #         {"status": "error", "message": "Chatbot configuration error"},
        #         status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        #     )

        twilio_sid = config("TWILIO_ACCOUNT_SID")
        twilio_token = config("TWILIO_AUTH_TOKEN")

        print("------------whatsapp_number-------------", whatsapp_number)
        print("--------whatsapp_sender_number-----------------", whatsapp_sender_number)
        print("------------reply-------------", reply)

        send_whatsapp_reply(
            twilio_sid=twilio_sid,
            twilio_token=twilio_token,
            to=whatsapp_number,
            from_=whatsapp_sender_number,
            body=reply,
        )

        return Response({"status": "ok"})


@method_decorator(csrf_exempt, name="dispatch")
class WhatsappStatusCallbackView(APIView):
    permission_classes = []

    def post(self, request, *args, **kwargs):
        print("request=================================>", request.data)
        return Response({"status": "ok"})


@method_decorator(csrf_exempt, name="dispatch")
class WhatsappFallbackView(APIView):
    permission_classes = []

    def post(self, request, *args, **kwargs):
        print("request=================================>", request.data)
        return Response({"status": "ok"})

import stripe
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from apps.billing.utils import handle_payment_failed, handle_payment_success
from apps.thirdparty.utils import create_twilio_subaccount, register_twilio_whatsapp_sender

from common.permissions import IsOwner


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


class WhatsappOnboardView(APIView):
    """
    Receives Embedded Signup result from frontend and registers the sender with Twilio.
    """

    permission_classes = [IsOwner]

    def post(self, request):
        waba_id = request.data.get("waba_id")
        phone_number = request.data.get("phone_number")
        customer_name = request.data.get("customer_name")

        if not waba_id or not phone_number:
            return Response(
                {"error": "Missing waba_id or phone_number"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        
        # Create a subaccount for the salon
        subaccount = create_twilio_subaccount(friendly_name=customer_name)

        # Register whatsapp sender on Twilio
        sender = register_twilio_whatsapp_sender(
            subaccount_sid=subaccount["account_sid"],
            subaccount_auth_token=subaccount["auth_token"],
            waba_id=waba_id,
            phone_number=phone_number,
        )

        return Response(
            {
                "subaccount": subaccount,
                "sender": sender,
            },
            status=status.HTTP_201_CREATED,
        )
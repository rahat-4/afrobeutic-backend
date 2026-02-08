import stripe
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.billing.utils import handle_payment_failed, handle_payment_success


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
    def post(self, request, *args, **kwargs):
        print("request=================================>", request)
        return Response({"status": "ok"})


@method_decorator(csrf_exempt, name="dispatch")
class WhatsappStatusCallbackView(APIView):
    def post(self, request, *args, **kwargs):
        print("request=================================>", request)
        return Response({"status": "ok"})


@method_decorator(csrf_exempt, name="dispatch")
class WhatsappFallbackView(APIView):
    def post(self, request, *args, **kwargs):
        print("request=================================>", request)
        return Response({"status": "ok"})

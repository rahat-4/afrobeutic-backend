from django.urls import path

from ..views.webhooks import (
    stripe_webhook,
    WhatsappCallbackView,
    WhatsappStatusCallbackView,
    WhatsappFallbackView,
)

urlpatterns = [
    path("/stripe", stripe_webhook, name="stripe-webhook"),
    path("/whatsapp-callback", WhatsappCallbackView.as_view(), name="whatsapp-chatbot"),
    path("/whatsapp-fallback", WhatsappFallbackView.as_view(), name="whatsapp-chatbot"),
    path(
        "/whatsapp-callback-status",
        WhatsappStatusCallbackView.as_view(),
        name="whatsapp-status",
    ),
]

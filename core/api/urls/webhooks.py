from django.urls import path

from ..views.webhooks import stripe_webhook, WhatsappOnboardView

urlpatterns = [
    path("/stripe", stripe_webhook, name="stripe-webhook"),
    path("/whatsapp/onboard", WhatsappOnboardView.as_view(), name="whatsapp-onboard"),
]

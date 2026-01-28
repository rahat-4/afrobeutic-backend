from django.urls import path

from apps.billing.webhook import stripe_webhook

urlpatterns = [
    path("/stripe", stripe_webhook, name="stripe-webhook"),
]

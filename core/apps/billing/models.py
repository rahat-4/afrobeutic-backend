from datetime import timedelta

from django.db import models
from django.utils import timezone
from django.db.models import UniqueConstraint
from django.db.models.functions import Lower

from common.models import BaseModel

from apps.authentication.models import Account

from .choices import (
    AccountCategory,
    SubscriptionStatus,
    PaymentTransactionStatus,
)


# Create your models here.
class PricingPlan(BaseModel):
    account_category = models.CharField(max_length=50, choices=AccountCategory.choices)
    name = models.CharField(max_length=255)
    price = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Monthly price in USD"
    )
    salon_limit = models.PositiveIntegerField(default=1)
    whatsapp_chatbot_limit = models.PositiveIntegerField(default=0)
    whatsapp_messages_per_chatbot = models.PositiveIntegerField(default=0)
    has_broadcasting = models.BooleanField(default=False)
    broadcasting_message_limit = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["account_category", "price"]
        constraints = [
            UniqueConstraint(
                Lower("name"),
                "account_category",
                name="unique_pricing_plan_name_per_category_ci",
            )
        ]

    def __str__(self):
        return f"{self.get_account_category_display()} - {self.name} (${self.price})"


class Subscription(BaseModel):
    status = models.CharField(
        max_length=20,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.TRIAL,
    )

    # Subscription dates
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    next_billing_date = models.DateTimeField(null=True, blank=True)

    # Auto-renewal
    auto_renew = models.BooleanField(default=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    notes = models.TextField(blank=True, null=True)

    # Fk
    pricing_plan = models.ForeignKey(
        PricingPlan, on_delete=models.PROTECT, related_name="pricing_plan_subscriptions"
    )
    account = models.OneToOneField(
        Account, on_delete=models.CASCADE, related_name="account_subscription"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.account.owner.email} - {self.pricing_plan}"

    @property
    def chatbot_limit(self):
        return self.pricing_plan.whatsapp_chatbot_limit

    @property
    def messages_per_chatbot(self):
        return self.pricing_plan.whatsapp_messages_per_chatbot


class Chatbot(BaseModel):
    name = models.CharField(max_length=100)
    messages_sent = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(default=True)

    # Fk
    subscription = models.ForeignKey(
        Subscription, on_delete=models.CASCADE, related_name="subscription_chatbots"
    )
    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="account_chatbots"
    )

    def __str__(self):
        return f"{self.name} ({self.subscription.account.user.username})"

    def message_limit(self):
        return self.subscription.messages_per_chatbot

    def has_remaining_messages(self):
        return self.messages_sent < self.message_limit()


class PaymentCard(BaseModel):
    card_token = models.CharField(max_length=255, help_text="Payment gateway token")
    last_four = models.CharField(max_length=4)
    card_brand = models.CharField(max_length=50)
    expiry_month = models.IntegerField()
    expiry_year = models.IntegerField()
    is_default = models.BooleanField(default=False)

    # Fk
    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="account_payment_cards"
    )

    def __str__(self):
        return f"{self.card_brand} ending in {self.last_four}"


class PaymentTransaction(BaseModel):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    transaction_id = models.CharField(max_length=255, unique=True)
    status = models.CharField(
        max_length=20,
        choices=PaymentTransactionStatus.choices,
        default=PaymentTransactionStatus.PENDING,
    )
    payment_method = models.CharField(max_length=50, blank=True, null=True)

    # Fk
    subscription = models.ForeignKey(
        Subscription, on_delete=models.CASCADE, related_name="transactions"
    )
    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="account_payment_transactions"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Transaction {self.transaction_id} - {self.amount} {self.currency}"

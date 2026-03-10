from django.db import models
from django.db.models import Q, UniqueConstraint
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
    # has_broadcasting = models.BooleanField(default=False)
    # broadcasting_message_limit = models.PositiveIntegerField(default=0)
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

    @property
    def total_messages(self):
        """Total messages across all chatbots for this plan."""
        return self.whatsapp_chatbot_limit * self.whatsapp_messages_per_chatbot

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

    # ── Stacked message balance ───────────────────────────────────────────────
    # When a plan changes (upgrade or downgrade), the unused messages from the
    # previous plan carry over and are added to the new plan's allowance.
    # This field is the single source of truth for how many messages remain.
    # It is initialised when the subscription is first created and updated on
    # every plan change inside perform_update().
    remaining_whatsapp_messages = models.PositiveIntegerField(
        default=0,
        help_text=(
            "Stacked remaining messages. On plan change: "
            "new_remaining = current_remaining + new_plan.total_messages"
        ),
    )

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

    def has_remaining_messages(self):
        return self.remaining_whatsapp_messages > 0

    def consume_message(self):
        """
        Decrement remaining_whatsapp_messages by 1 atomically.
        Call this each time the bot sends a reply.
        Returns True if the message was allowed, False if quota was exhausted.
        """
        updated = Subscription.objects.filter(
            pk=self.pk,
            remaining_whatsapp_messages__gt=0,
        ).update(
            remaining_whatsapp_messages=models.F("remaining_whatsapp_messages") - 1
        )
        return updated > 0

    def stack_messages(self, new_plan: PricingPlan) -> int:
        """
        Add new_plan.total_messages on top of the current balance.
        Saves and returns the new total.
        Used on renewal AND plan upgrade/downgrade.
        """
        new_remaining = self.remaining_whatsapp_messages + new_plan.total_messages
        Subscription.objects.filter(pk=self.pk).update(
            remaining_whatsapp_messages=new_remaining
        )
        self.remaining_whatsapp_messages = new_remaining
        return new_remaining


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

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["account"],
                condition=Q(is_default=True),
                name="unique_default_card_per_account",
            )
        ]

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
    # Track which attempt this was (0 = initial, 1–3 = retries)
    attempt_number = models.PositiveSmallIntegerField(default=0)

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

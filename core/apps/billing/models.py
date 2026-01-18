from datetime import timedelta

from django.db import models
from django.utils import timezone

from common.models import BaseModel

from apps.authentication.models import Account

from .choices import (
    AccountCategory,
    PlanType,
    SubscriptionStatus,
    PaymentTransactionStatus,
)


# Create your models here.
class PricingPlan(BaseModel):
    account_category = models.CharField(max_length=50, choices=AccountCategory.choices)
    plan_type = models.CharField(max_length=20, choices=PlanType.choices)
    price = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Monthly price in USD"
    )
    salon_count = models.IntegerField(default=1)
    whatsapp_chatbot_count = models.IntegerField(default=0)
    whatsapp_messages_limit = models.IntegerField(
        default=0, help_text="Messages per chatbot"
    )
    has_broadcasting = models.BooleanField(default=False)
    broadcasting_message_limit = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ["account_category", "plan_type"]
        ordering = ["account_category", "price"]

    def __str__(self):
        return f"{self.get_account_category_display()} - {self.get_plan_type_display()}"


class Subscription(BaseModel):
    status = models.CharField(
        max_length=20,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.TRIAL,
    )

    # Trial information
    trial_start_date = models.DateTimeField(null=True, blank=True)
    trial_end_date = models.DateTimeField(null=True, blank=True)

    # Subscription dates
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    next_billing_date = models.DateTimeField(null=True, blank=True)

    # Custom plan pricing (for custom plans only)
    custom_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    custom_salon_count = models.IntegerField(null=True, blank=True)
    custom_chatbot_count = models.IntegerField(null=True, blank=True)
    custom_messages_limit = models.IntegerField(null=True, blank=True)
    custom_broadcasting_limit = models.IntegerField(null=True, blank=True)

    # Usage tracking
    salons_created = models.IntegerField(default=0)
    chatbots_created = models.IntegerField(default=0)
    messages_used = models.IntegerField(default=0)
    broadcasts_sent = models.IntegerField(default=0)

    # Auto-renewal
    auto_renew = models.BooleanField(default=True)

    # Metadata
    notes = models.TextField(blank=True, null=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    # Fk
    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="account_subscriptions"
    )
    pricing_plan = models.ForeignKey(
        PricingPlan, on_delete=models.PROTECT, related_name="pricing_plan_subscriptions"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.account.user.username} - {self.pricing_plan}"

    def is_trial_active(self):
        """Check if trial is still active"""
        if self.status == SubscriptionStatus.TRIAL and self.trial_end_date:
            return timezone.now() < self.trial_end_date
        return False

    def is_active(self):
        """Check if subscription is active"""
        if self.status == SubscriptionStatus.TRIAL:
            return self.is_trial_active()
        elif self.status == SubscriptionStatus.ACTIVE and self.end_date:
            return timezone.now() < self.end_date
        return False

    def get_salon_limit(self):
        """Get salon limit based on plan or custom settings"""
        if self.pricing_plan.plan_type == PlanType.CUSTOM and self.custom_salon_count:
            return self.custom_salon_count
        return self.pricing_plan.salon_count

    def get_chatbot_limit(self):
        """Get chatbot limit based on plan or custom settings"""
        if self.pricing_plan.plan_type == PlanType.CUSTOM and self.custom_chatbot_count:
            return self.custom_chatbot_count
        return self.pricing_plan.whatsapp_chatbot_count

    def get_messages_limit(self):
        """Get messages limit based on plan or custom settings"""
        if (
            self.pricing_plan.plan_type == PlanType.CUSTOM
            and self.custom_messages_limit
        ):
            return self.custom_messages_limit
        return self.pricing_plan.whatsapp_messages_limit

    def get_broadcasting_limit(self):
        """Get broadcasting limit based on plan or custom settings"""
        if (
            self.pricing_plan.plan_type == PlanType.CUSTOM
            and self.custom_broadcasting_limit
        ):
            return self.custom_broadcasting_limit
        return self.pricing_plan.broadcasting_message_limit

    def start_trial(self):
        """Initialize trial subscription"""
        self.status = SubscriptionStatus.TRIAL
        self.trial_start_date = timezone.now()
        self.trial_end_date = timezone.now() + timedelta(days=30)
        self.save()

    def activate_paid_subscription(self):
        """Convert from trial to paid subscription"""
        self.status = SubscriptionStatus.ACTIVE
        self.start_date = timezone.now()
        self.end_date = timezone.now() + timedelta(days=30)
        self.next_billing_date = self.end_date
        self.save()


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

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Transaction {self.transaction_id} - {self.amount} {self.currency}"

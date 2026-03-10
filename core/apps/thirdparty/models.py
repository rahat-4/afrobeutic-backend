from django.contrib.auth import get_user_model
from django.db import models

from common.models import BaseModel

from apps.salon.models import Account, Salon, Customer

from .choices import WhatsappChatbotMessageRole

User = get_user_model()


class WhatsappChatbotConfig(BaseModel):
    waba_id = models.JSONField(default=dict)
    phone_number_id = models.JSONField(default=dict)
    access_token = models.JSONField(default=dict)
    account_sid = models.JSONField(default=dict)
    auth_token = models.JSONField(default=dict)
    whatsapp_number = models.CharField(max_length=50, unique=True, db_index=True)
    sender_sid = models.CharField(max_length=255)
    status = models.CharField(max_length=255)
    assistant_id = models.JSONField(default=dict, blank=True, null=True)
    chatbot_name = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_chatbot_configs",
    )
    salon = models.OneToOneField(
        Salon,
        on_delete=models.CASCADE,
        related_name="salon_chatbot_config",
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name="account_chatbot_config",
    )

    # ── Billing helpers ───────────────────────────────────────────────────────

    def messages_sent_count(self):
        return self.messages.count()

    def remaining_messages(self):
        from apps.billing.models import Subscription

        try:
            plan_limit = (
                self.account.account_subscription.pricing_plan.whatsapp_messages_per_chatbot
            )
        except Subscription.DoesNotExist:
            return 0
        return max(plan_limit - self.messages_sent_count(), 0)

    def has_remaining_messages(self) -> bool:
        """
        Delegates to Subscription.remaining_whatsapp_messages — the stacked
        balance that carries over across plan changes.
        """
        try:
            return self.account.account_subscription.has_remaining_messages()
        except Exception:
            return False

    def consume_message(self) -> bool:
        """
        Atomically decrement the account's stacked message balance by 1.
        Returns True if allowed, False if quota exhausted.
        Call this AFTER the bot reply is generated, before sending.
        """
        try:
            return self.account.account_subscription.consume_message()
        except Exception:
            return False

    def __str__(self):
        return f"WhatsappChatbotConfig — {self.salon.name}"

    def __str__(self):
        return f"WhatsappChatbotConfig — {self.salon.name}"


class WhatsappChatbotMessageLog(BaseModel):
    message = models.TextField()
    media_url = models.URLField(blank=True, null=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    role = models.CharField(
        max_length=20,
        choices=WhatsappChatbotMessageRole.choices,
    )

    # Fk Relationships
    chatbot = models.ForeignKey(
        WhatsappChatbotConfig, on_delete=models.CASCADE, related_name="messages"
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="customer_whatsapp_messages",
    )
    admin = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="admin_whatsapp_messages",
    )

    class Meta:
        ordering = ["sent_at"]

    def __str__(self):
        return f"[{self.role}] {self.customer} — {self.sent_at:%Y-%m-%d %H:%M}"

from django.contrib.auth import get_user_model
from django.db import models

from common.models import BaseModel

from apps.salon.models import Account, Salon, Customer

from .choices import (
    WhatsappChatbotStatus,
    WhatsappChatbotMessageRole,
    WhatsappSenderStatus,
)

User = get_user_model()


class MetaConfig(BaseModel):
    waba_id = models.JSONField(default=dict)
    account_sid = models.JSONField(default=dict)
    auth_token = models.JSONField(default=dict)

    account = models.OneToOneField(
        Account,
        on_delete=models.CASCADE,
        related_name="account_meta_config",
    )


class WhatsappChatbotConfig(BaseModel):
    chatbot_name = models.CharField(max_length=255, blank=True, null=True)
    sender_sid = models.JSONField(default=dict)
    assistant_id = models.JSONField(default=dict, blank=True, null=True)
    whatsapp_sender_number = models.CharField(max_length=100)
    status = models.CharField(max_length=100)

    # Fk
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_whatsapp_chatbot_configs",
    )
    salon = models.OneToOneField(
        Salon, on_delete=models.CASCADE, related_name="salon_whatsapp_chatbot_config"
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name="account_whatsapp_chatbot_configs",
    )

    def messages_sent_count(self):
        """Return number of messages sent by this chatbot"""
        return self.messages.count()

    def remaining_messages(self):
        """
        Return remaining messages allowed for this chatbot based on plan
        """
        plan_limit = self.account.pricing_plan.whatsapp_messages_per_chatbot
        return max(plan_limit - self.messages_sent_count(), 0)

    def has_remaining_messages(self):
        """Check if this chatbot can send more messages"""
        return self.remaining_messages() > 0

    def __str__(self):
        return f"WhatsappChatbotConfig for Account: {self.salon.name }"


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

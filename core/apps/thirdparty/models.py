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


class TwilioConfig(BaseModel):
    sender_sid = models.JSONField(default=dict)
    whatsapp_sender_number = models.CharField(max_length=100)
    sender_status = models.CharField(max_length=100)

    # Fk
    salon = models.OneToOneField(
        Salon, on_delete=models.CASCADE, related_name="salon_twilio_config"
    )
    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="account_twilio_configs"
    )

    def __str__(self):
        return f"TwilioConfig for Account: {self.sender_sid}"


class WhatsappChatbotConfig(BaseModel):
    status = models.CharField(
        max_length=20,
        choices=WhatsappChatbotStatus.choices,
        default=WhatsappChatbotStatus.ACTIVE,
    )

    # Foreign Key and OneToOne Relationships
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="created_whatsapp_chatbot_configs",
    )
    twilio = models.OneToOneField(
        TwilioConfig,
        on_delete=models.CASCADE,
        related_name="twilio_whatsapp_chatbot_configs",
    )
    salon = models.OneToOneField(
        Salon, on_delete=models.CASCADE, related_name="salon_whatsapp_chatbot_configs"
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name="account_whatsapp_chatbot_configs",
    )

    def __str__(self):
        return f"WhatsappChatbotConfig for Salon: {self.salon.name} (Status: {self.status})"


class WhatsappChatbotMessageLog(BaseModel):
    content = models.TextField()
    media_url = models.URLField(blank=True, null=True)
    role = models.CharField(
        max_length=20,
        choices=WhatsappChatbotMessageRole.choices,
    )
    note = models.TextField(blank=True, null=True)  # Delete it later

    # Fk Relationships
    chatbot = models.ForeignKey(
        WhatsappChatbotConfig, on_delete=models.CASCADE, related_name="messages"
    )
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="whatsapp_messages"
    )
    admin = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="admin_whatsapp_messages",
    )

from simple_history.models import HistoricalRecords

from django.contrib.auth import get_user_model
from django.db import models

from common.models import BaseModel

from apps.authentication.models import Account
from apps.salon.models import Salon, Customer

from .choices import OpenaiGptModel, WhatsappChatbotStatus, WhatsappChatbotMessageRole

User = get_user_model()


class OpenaiConfig(BaseModel):
    api_key = models.TextField()
    gpt_model = models.CharField(
        max_length=100,
        choices=OpenaiGptModel.choices,
        default=OpenaiGptModel.GPT_4O,
    )
    welcome_message_instruction = models.TextField(blank=True, null=True)
    suggest_available_time = models.BooleanField(default=False)

    # OnetoOne and Foreign Key Relationships
    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="openai_conf"
    )  # confusion here, Is one twilio conf per account?


class TwilioConf(BaseModel):
    account_sid = models.TextField()
    auth_token = models.TextField()
    messaging_service_sid = models.TextField()
    whatsapp_sender_number = models.CharField(max_length=20)
    webhook_url = models.URLField()

    # Foreign Key Relationships
    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="twilio_conf"
    )  # confusion here, Is one twilio conf per account?

    # Why message templates relation here?

    def __str__(self):
        return f"TwilioConf for Account: {self.account.name}"


class TwilioTemplate(BaseModel):
    content_sid = models.TextField()
    content_text = models.TextField()
    content_variables = models.JSONField(default=list, blank=True)

    # Foreign Key Relationships
    twilio_conf = models.ForeignKey(
        TwilioConf, on_delete=models.CASCADE, related_name="message_templates"
    )


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
        TwilioConf,
        on_delete=models.CASCADE,
        related_name="twilio_whatsapp_chatbot_configs",
    )
    openai = models.OneToOneField(
        OpenaiConfig,
        on_delete=models.CASCADE,
        related_name="openai_whatsapp_chatbot_configs",
    )
    salon = models.OneToOneField(
        Salon, on_delete=models.CASCADE, related_name="salon_whatsapp_chatbot_configs"
    )

    history = HistoricalRecords()

    def __str__(self):
        return f"WhatsappChatbotConfig for Salon: {self.salon.name} (Status: {self.status})"


class WhatsappChatbotMessageLog(BaseModel):
    content = models.TextField()
    media_url = models.URLField(blank=True, null=True)
    role = models.CharField(
        max_length=20,
        choices=WhatsappChatbotMessageRole.choices,
        default=WhatsappChatbotMessageRole.USER,
    )

    # One-to-One Relationships
    admin = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        related_name="admin_message_logs",
        null=True,
        blank=True,
    )
    customer = models.OneToOneField(
        Customer,
        on_delete=models.CASCADE,
        related_name="customer_message_logs",
    )

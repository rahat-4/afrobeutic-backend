from rest_framework import serializers

from apps.thirdparty.choices import WhatsappChatbotMessageRole
from apps.thirdparty.models import TwilioConf, TwilioTemplate


class TwilioTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TwilioTemplate
        fields = [
            "uid",
            "content_sid",
            "content_text",
            "content_variables",
            "created_at",
            "updated_at",
        ]


class TwilioConfSerializer(serializers.ModelSerializer):
    message_templates = TwilioTemplateSerializer(many=True, read_only=True)

    class Meta:
        model = TwilioConf
        fields = [
            "uid",
            "account_sid",
            "auth_token",
            "messaging_service_sid",
            "whatsapp_sender_number",
            "webhook_url",
            "message_templates",
            "created_at",
            "updated_at",
        ]

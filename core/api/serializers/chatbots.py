from rest_framework import serializers

from apps.thirdparty.models import WhatsappChatbotConfig


class WhatsappChatbotConfigSerializer(serializers.ModelSerializer):
    salon = serializers.CharField(source="salon.name", read_only=True)

    class Meta:
        model = WhatsappChatbotConfig
        fields = ["chatbot_name", "whatsapp_sender_number", "status", "salon"]

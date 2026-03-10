from rest_framework import serializers

from apps.thirdparty.models import WhatsappChatbotConfig


class WhatsappChatbotConfigSerializer(serializers.ModelSerializer):
    salon = serializers.CharField(source="salon.name", read_only=True)
    message_limit = serializers.SerializerMethodField()
    remaining_messages = serializers.SerializerMethodField()

    class Meta:
        model = WhatsappChatbotConfig
        fields = [
            "chatbot_name",
            "whatsapp_number",
            "status",
            "message_limit",
            "remaining_messages",
            "salon",
        ]

    def get_message_limit(self, obj):
        from apps.billing.models import Subscription

        try:
            return (
                obj.account.account_subscription.pricing_plan.whatsapp_messages_per_chatbot
            )
        except Subscription.DoesNotExist:
            return 0

    def get_remaining_messages(self, obj):
        return obj.remaining_messages()

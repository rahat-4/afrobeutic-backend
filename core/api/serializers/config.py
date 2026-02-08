# from rest_framework import serializers


# from apps.salon.models import Salon
# from apps.thirdparty.choices import WhatsappChatbotMessageRole
# from apps.thirdparty.models import TwilioConfig, OpenaiConfig, WhatsappChatbotConfig, WhatsappChatbotMessageLog

# class TwilioConfigSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = TwilioConfig
#         fields = [
#             "uid",
#             "account_sid",
#             "auth_token",
#             "sender_sid",
#             "whatsapp_sender_number",
#             "webhook_url",
#         ]

# class OpenaiConfigSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = OpenaiConfig
#         fields = [
#             "uid",
#             "api_key",
#             "gpt_model",
#             "welcome_message_instruction",
#             "suggest_available_time",
#         ]


# class WhatsappChatbotConfigSerializer(serializers.ModelSerializer):
#     salon = serializers.SlugRelatedField(slug_field="uid", queryset=Salon.objects.all(), write_only=True)
#     twilio = TwilioConfigSerializer()
#     openai = OpenaiConfigSerializer()

#     class Meta:
#         model = WhatsappChatbotConfig
#         fields = [
#             "uid",
#             "salon",
#             "status",
#             "twilio",
#             "openai",
#             "created_by",
#             "created_at",
#         ]
#         read_only_fields = ["created_by"]

#     def create(self, validated_data):
#         account = self.context["request"].account
#         salon = validated_data.pop("salon")
#         twilio_data = validated_data.pop("twilio")
#         openai_data = validated_data.pop("openai")


#         twilio = TwilioConfig.objects.create(**twilio_data)
#         openai = OpenaiConfig.objects.create(**openai_data)

#         chatbot = WhatsappChatbotConfig.objects.create(
#             twilio=twilio,
#             openai=openai,
#             salon=salon,
#             account=account,
#             **validated_data
#         )
#         return chatbot


# class WhatsappChatbotMessageLogSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = WhatsappChatbotMessageLog
#         fields = [
#             "uid",
#             "content",
#             "media_url",
#             "role",
#             "chatbot",
#             "customer",
#             "admin",
#             "created_at",
#         ]

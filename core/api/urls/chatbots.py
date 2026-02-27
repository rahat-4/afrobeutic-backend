from django.urls import path

from ..views.chatbots import WhatsappChatbotConfigListAPIView

urlpatterns = [
    path(
        "",
        WhatsappChatbotConfigListAPIView.as_view(),
        name="whatsapp-chatbot-config-list",
    ),
]

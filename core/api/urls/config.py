from django.urls import path

from ..views.config import (
    WhatsappChatbotListView,
    WhatsappChatbotDetailView,
    WhatsappChatbotMessageListView,
)

urlpatterns = [
    path(
        "/chatbot/<uuid:chatbot_uid>/messages",
        WhatsappChatbotMessageListView.as_view(),
    ),
    path("/chatbot/<uuid:chatbot_uid>", WhatsappChatbotDetailView.as_view()),
    path("/chatbot", WhatsappChatbotListView.as_view()),
]

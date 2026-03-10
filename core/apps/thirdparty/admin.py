from django.contrib import admin

from .models import (
    WhatsappChatbotConfig,
    WhatsappChatbotMessageLog,
)

admin.site.register(WhatsappChatbotConfig)
admin.site.register(WhatsappChatbotMessageLog)

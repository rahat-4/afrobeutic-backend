from django.contrib import admin

from .models import (
    WhatsappChatbotConfig,
    WhatsappChatbotMessageLog,
    WhatsappThreadMapping,
)

admin.site.register(WhatsappChatbotConfig)
admin.site.register(WhatsappThreadMapping)
admin.site.register(WhatsappChatbotMessageLog)

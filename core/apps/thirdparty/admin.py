from django.contrib import admin

from .models import (
    OpenaiConfig,
    TwilioConf,
    TwilioTemplate,
    WhatsappChatbotConfig,
    WhatsappChatbotMessageLog,
)

admin.site.register(OpenaiConfig)
admin.site.register(TwilioConf)
admin.site.register(TwilioTemplate)
admin.site.register(WhatsappChatbotConfig)
admin.site.register(WhatsappChatbotMessageLog)

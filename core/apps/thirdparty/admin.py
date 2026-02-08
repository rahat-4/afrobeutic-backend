from django.contrib import admin

from .models import (
    # OpenaiConfig,
    MetaConfig,
    TwilioConfig,
    # TwilioTemplate,
    # WhatsappChatbotConfig,
    # WhatsappChatbotMessageLog,
)

# admin.site.register(OpenaiConfig)
admin.site.register(MetaConfig)
admin.site.register(TwilioConfig)
# admin.site.register(TwilioTemplate)
# admin.site.register(WhatsappChatbotConfig)
# admin.site.register(WhatsappChatbotMessageLog)

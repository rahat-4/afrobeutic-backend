from django.db import models


class OpenaiGptModel(models.TextChoices):
    GPT_3_5_TURBO = "gpt-3.5-turbo", "GPT-3.5 Turbo"
    GPT_4 = "gpt-4", "GPT-4"
    GPT_4_TURBO = "gpt-4-turbo", "GPT-4 Turbo"
    GPT_4O = "gpt-4o", "GPT-4o"
    GPT_4O_MINI = "gpt-4o-mini", "GPT-4o Mini"


class WhatsappChatbotStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    PAUSED = "PAUSED", "Paused"
    DELETED = "DELETED", "Deleted"


class WhatsappChatbotMessageRole(models.TextChoices):
    USER = "USER", "User"
    BOT = "BOT", "Bot"
    ADMIN = "ADMIN", "Admin"

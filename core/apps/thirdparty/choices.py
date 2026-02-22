from django.db import models


class WhatsappChatbotStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    PAUSED = "PAUSED", "Paused"
    DELETED = "DELETED", "Deleted"


class WhatsappChatbotMessageRole(models.TextChoices):
    USER = "USER", "User"
    BOT = "BOT", "Bot"
    ADMIN = "ADMIN", "Admin"


class WhatsappSenderStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    INACTIVE = "INACTIVE", "Inactive"

from django.db import models


class WhatsappChatbotMessageRole(models.TextChoices):
    CUSTOMER = "CUSTOMER", "Customer"
    BOT = "BOT", "Bot"
    ADMIN = "ADMIN", "Admin"

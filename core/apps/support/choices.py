from django.db import models


class SupportTicketLevel(models.TextChoices):
    LOW = "LOW", "Low"
    MEDIUM = "MEDIUM", "Medium"
    HIGH = "HIGH", "High"
    URGENT = "URGENT", "Urgent"


class SupportTicketTopic(models.TextChoices):
    ACCOUNT = "ACCOUNT", "Account"
    SALON_MANAGEMENT = "SALON_MANAGEMENT", "Salon Management"
    CHATBOTS = "CHATBOTS", "Chatbots"
    CLIENT_REQUESTS = "CLIENT_REQUESTS", "Client Requests"
    OTHERS = "OTHERS", "Others"

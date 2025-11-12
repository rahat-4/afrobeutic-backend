from django.db import models
from django.utils.translation import gettext_lazy as _


class SupportTicketLevel(models.TextChoices):
    LOW = "LOW", _("Low")
    MEDIUM = "MEDIUM", _("Medium")
    HIGH = "HIGH", _("High")
    URGENT = "URGENT", _("Urgent")


class SupportTicketTopic(models.TextChoices):
    ACCOUNT = "ACCOUNT", _("Account")
    SALON_MANAGEMENT = "SALON_MANAGEMENT", _("Salon Management")
    CHATBOTS = "CHATBOTS", _("Chatbots")
    CLIENT_REQUESTS = "CLIENT_REQUESTS", _("Client Requests")
    OTHERS = "OTHERS", _("Others")


class SupportTicketStatus(models.TextChoices):
    NEW = "NEW", _("New")
    IN_REVIEW = "IN_REVIEW", _("In Review")
    CANCELLED = "CANCELLED", _("Cancelled")
    RESOLVED = "RESOLVED", _("Resolved")


class QueryType(models.TextChoices):
    EMERGENCY = "EMERGENCY", _("Emergency")
    GENERAL = "GENERAL", _("General")

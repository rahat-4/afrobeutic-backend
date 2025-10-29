from django.db import models

from common.models import BaseModel
from apps.authentication.models import Account

from .choices import SupportTicketTopic, SupportTicketLevel


class SupportTicket(BaseModel):
    level = models.CharField(
        max_length=50,
        choices=SupportTicketLevel.choices,
        default=SupportTicketLevel.LOW,
    )
    topic = models.CharField(
        max_length=50,
        choices=SupportTicketTopic.choices,
        default=SupportTicketTopic.OTHERS,
    )
    subject = models.CharField(max_length=255)
    queries = models.TextField()

    # Fk
    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="support_tickets"
    )

    def __str__(self):
        return self.subject

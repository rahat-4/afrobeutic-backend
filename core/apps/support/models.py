from django.db import models

from common.models import BaseModel

from apps.authentication.models import Account
from apps.salon.models import Salon, Customer

from .choices import (
    SupportTicketTopic,
    SupportTicketLevel,
    SupportTicketStatus,
    QueryType,
)


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
    status = models.CharField(
        max_length=20,
        choices=SupportTicketStatus.choices,
        default=SupportTicketStatus.NEW,
    )

    # Fk
    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="support_tickets"
    )

    def __str__(self):
        return self.subject


class AccountSupportTicket(BaseModel):
    type = models.CharField(
        max_length=20,
        choices=QueryType.choices,
        default=QueryType.GENERAL,
    )
    summary = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=SupportTicketStatus.choices,
        default=SupportTicketStatus.NEW,
    )

    # Fk
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="customer_queries",
    )
    salon = models.ForeignKey(
        Salon, on_delete=models.CASCADE, related_name="salon_queries"
    )
    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="account_queries"
    )

    def __str__(self):
        return f"Query {self.uid} - {self.type}"

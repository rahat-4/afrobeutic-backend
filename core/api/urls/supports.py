from django.urls import path

from ..views.supports import (
    SupportTicketListView,
    SupportTicketDetailView,
    AccountSupportTicketListView,
    AccountSupportTicketDetailView,
)

urlpatterns = [
    path(
        "/account/<uuid:account_support_ticket_uid>",
        AccountSupportTicketDetailView.as_view(),
        name="account-support-ticket.detail",
    ),
    path(
        "/account",
        AccountSupportTicketListView.as_view(),
        name="account-support-ticket.list",
    ),
    path(
        "/<uuid:support_ticket_uid>",
        SupportTicketDetailView.as_view(),
        name="support-ticket.detail",
    ),
    path("", SupportTicketListView.as_view(), name="support-ticket.list"),
]

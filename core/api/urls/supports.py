from django.urls import path

from ..views.supports import SupportTicketListView, SupportTicketDetailView

urlpatterns = [
    path(
        "/<uuid:support_ticket_uid>",
        SupportTicketDetailView.as_view(),
        name="support-ticket.detail",
    ),
    path("", SupportTicketListView.as_view(), name="support-ticket.list"),
]

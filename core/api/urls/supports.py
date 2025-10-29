from django.urls import path

from ..views.supports import SupportTicketListView

urlpatterns = [
    path("", SupportTicketListView.as_view(), name="support-ticket.list"),
]

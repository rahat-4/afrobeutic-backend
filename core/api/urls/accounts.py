from django.urls import path

from ..views.accounts import (
    AccountInvitationView,
    AccountListView,
)

urlpatterns = [
    path(
        "/invite",
        AccountInvitationView.as_view(),
        name="account.invite",
    ),
    path("", AccountListView.as_view(), name="account.list"),
]

from django.urls import path

from ..views.accounts import (
    AccountMemberDetailView,
    AccountMemberListView,
    AccountInvitationView,
    AccountAccessListView,
)

urlpatterns = [
    path("/access", AccountAccessListView.as_view(), name="member-account.list"),
    path(
        "/invite",
        AccountInvitationView.as_view(),
        name="account.invite",
    ),
    path(
        "/members/<uuid:member_uid>",
        AccountMemberDetailView.as_view(),
        name="account.member-detail",
    ),
    path("/members", AccountMemberListView.as_view(), name="account.list"),
]

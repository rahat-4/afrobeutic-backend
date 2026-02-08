from django.urls import path

from ..views.accounts import (
    AccountMemberDetailView,
    AccountMemberListView,
    AccountInvitationView,
    AccountAccessListView,
    AccountPricingPlanDetailView,
    AccountPricingPlanListView,
    AccountSubscriptionDetailView,
    AccountMetaConfigView,
)


urlpatterns = [
    path(
        "/meta-config",
        AccountMetaConfigView.as_view(),
        name="account.meta-config",
    ),
    path(
        "/subscription",
        AccountSubscriptionDetailView.as_view(),
        name="account.subscription-detail",
    ),
    path(
        "/pricing-plans/<uuid:pricing_plan_uid>",
        AccountPricingPlanDetailView.as_view(),
        name="account.pricing-plan-detail",
    ),
    path(
        "/pricing-plans",
        AccountPricingPlanListView.as_view(),
        name="account.pricing-plan-list",
    ),
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

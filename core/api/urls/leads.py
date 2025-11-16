from django.urls import path

from ..views.leads import AccountLeadDetailView, AccountLeadListView

urlpatterns = [
    path(
        "/<uuid:lead_uid>",
        AccountLeadDetailView.as_view(),
        name="account-lead-detail",
    ),
    path(
        "",
        AccountLeadListView.as_view(),
        name="account-lead-list",
    ),
]

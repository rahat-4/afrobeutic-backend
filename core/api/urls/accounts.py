from django.urls import path

from ..views.accounts import AccountListView

urlpatterns = [
    path("", AccountListView.as_view(), name="account.list"),
]

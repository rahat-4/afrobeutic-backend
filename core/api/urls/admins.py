from django.urls import path

from ..views.admins import AdminUserListView, AdminAccountListView

urlpatterns = [
    path("/users", AdminUserListView.as_view(), name="admin.users"),
    path("/accounts", AdminAccountListView.as_view(), name="admin.accounts"),
]

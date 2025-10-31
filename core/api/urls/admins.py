from django.urls import path

from ..views.admins import AdminUserListView

urlpatterns = [
    path("/users", AdminUserListView.as_view(), name="admin.users"),
]

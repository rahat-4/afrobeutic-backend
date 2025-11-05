from django.urls import path

from ..views.admins import (
    AdminUserListView,
    AdminAccountListView,
    AdminSalonListView,
    AdminSalonDetailView,
)

urlpatterns = [
    path("/users", AdminUserListView.as_view(), name="admin.users"),
    path("/accounts", AdminAccountListView.as_view(), name="admin.accounts"),
    path(
        "/salons",
        AdminSalonListView.as_view(),
        name="admin.salons",
    ),
    path(
        "/salons/<uuid:salon_uid>",
        AdminSalonDetailView.as_view(),
        name="admin.salon-detail",
    ),
]

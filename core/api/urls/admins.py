from django.urls import path

from ..views.admins import (
    AdminUserListView,
    AdminAccountListView,
    AdminSalonListView,
    AdminSalonDetailView,
    AdminServiceListView,
)

urlpatterns = [
    path(
        "/salons/<uuid:salon_uid>/services",
        AdminServiceListView.as_view(),
        name="admin.salon-services",
    ),
    path(
        "/salons/<uuid:salon_uid>",
        AdminSalonDetailView.as_view(),
        name="admin.salon-detail",
    ),
    path(
        "/salons",
        AdminSalonListView.as_view(),
        name="admin.salons",
    ),
    path("/accounts", AdminAccountListView.as_view(), name="admin.accounts"),
    path("/users", AdminUserListView.as_view(), name="admin.users"),
]

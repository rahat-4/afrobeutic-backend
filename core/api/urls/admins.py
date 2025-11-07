from django.urls import path

from ..views.admins import (
    AdminRegistrationView,
    AdminUserListView,
    AdminAccountListView,
    AdminSalonListView,
    AdminSalonDetailView,
    AdminServiceListView,
    AdminProductListView,
    AdminEmployeeListView,
    AdminBookingListView,
    AdminManagementListView,
)

urlpatterns = [
    path(
        "/salons/<uuid:salon_uid>/bookings",
        AdminBookingListView.as_view(),
        name="admin.salon-bookings",
    ),
    path(
        "/salons/<uuid:salon_uid>/employees",
        AdminEmployeeListView.as_view(),
        name="admin.salon-employees",
    ),
    path(
        "/salons/<uuid:salon_uid>/products",
        AdminProductListView.as_view(),
        name="admin.salon-products",
    ),
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
    path("/managements", AdminManagementListView.as_view(), name="admin.management"),
    path(
        "/register",
        AdminRegistrationView.as_view(),
        name="auth.admin-register",
    ),
]

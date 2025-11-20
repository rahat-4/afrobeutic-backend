from django.urls import path

from ..views.admin import (
    AdminRegistrationView,
    AdminUserListView,
    AdminAccountListView,
    AdminSalonListView,
    AdminSalonDetailView,
    AdminAccountEnquiryListView,
    AdminAccountEnquiryDetailView,
    AdminServiceListView,
    AdminProductListView,
    AdminEmployeeListView,
    AdminBookingListView,
    AdminManagementListView,
    AdminSubscriptionPlanListView,
)

urlpatterns = [
    path(
        "/subscription-plans",
        AdminSubscriptionPlanListView.as_view(),
        name="admin.subscription-plans",
    ),
    path(
        "/accounts/<uuid:account_uid>/salons/<uuid:salon_uid>/bookings",
        AdminBookingListView.as_view(),
        name="admin.account-salon-bookings",
    ),
    path(
        "/accounts/<uuid:account_uid>/salons/<uuid:salon_uid>/employees",
        AdminEmployeeListView.as_view(),
        name="admin.account-salon-employees",
    ),
    path(
        "/accounts/<uuid:account_uid>/salons/<uuid:salon_uid>/products",
        AdminProductListView.as_view(),
        name="admin.account-salon-products",
    ),
    path(
        "/accounts/<uuid:account_uid>/salons/<uuid:salon_uid>/services",
        AdminServiceListView.as_view(),
        name="admin.account-salon-services",
    ),
    path(
        "/accounts/<uuid:account_uid>/salons/<uuid:salon_uid>",
        AdminSalonDetailView.as_view(),
        name="admin.account-salon-detail",
    ),
    path(
        "/accounts/<uuid:account_uid>/salons",
        AdminSalonListView.as_view(),
        name="admin.account-salons",
    ),
    path(
        "/accounts/<uuid:account_uid>/enquiries/<uuid:account_enquiry_uid>",
        AdminAccountEnquiryDetailView.as_view(),
        name="admin.account-enquiry-detail",
    ),
    path(
        "/accounts/<uuid:account_uid>/enquiries",
        AdminAccountEnquiryListView.as_view(),
        name="admin.account-enquiry-list",
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

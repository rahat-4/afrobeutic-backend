from django.urls import path

from ..views.supports import (
    AccountEnquiryListView,
    AccountEnquiryDetailView,
    CustomerEnquiryListView,
    CustomerEnquiryDetailView,
)

urlpatterns = [
    path(
        "/customer-enquiries/<uuid:customer_enquiry_uid>",
        CustomerEnquiryDetailView.as_view(),
        name="customer-enquiry.detail",
    ),
    path(
        "/customer-enquiries",
        CustomerEnquiryListView.as_view(),
        name="customer-enquiry.list",
    ),
    path(
        "/account-enquiries/<uuid:account_enquiry_uid>",
        AccountEnquiryDetailView.as_view(),
        name="account-enquiry.detail",
    ),
    path(
        "/account-enquiries",
        AccountEnquiryListView.as_view(),
        name="account-enquiry.list",
    ),
]

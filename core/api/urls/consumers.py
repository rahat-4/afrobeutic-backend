from django.urls import path

from ..views.consumers import (
    CustomerProfileView,
    CustomerBookingListView,
    CustomerBookingDetailView,
    CustomerReceiptDownloadAPIView,
)

urlpatterns = [
    path(
        "/profile",
        CustomerProfileView.as_view(),
        name="customer.profile",
    ),
    path(
        "/bookings",
        CustomerBookingListView.as_view(),
        name="customer.bookings",
    ),
    path(
        "/bookings/<uuid:booking_uid>",
        CustomerBookingDetailView.as_view(),
        name="customer.booking.detail",
    ),
    path(
        "/bookings/<uuid:booking_uid>/receipt",
        CustomerReceiptDownloadAPIView.as_view(),
        name="customer.booking.receipt",
    ),
]

from django.urls import path

from ..views.public import PublicBookingListView

urlpatterns = [
    path(
        "/bookings",
        PublicBookingListView.as_view(),
        name="public.booking-list",
    ),
]
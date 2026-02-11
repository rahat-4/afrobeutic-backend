from django.urls import path

from ..views.public import (
    PublicSalonListView,
    PublicSalonDetailView,
    PublicSalonBookingView,
)

urlpatterns = [
    path("/salons", PublicSalonListView.as_view(), name="public.salon-list"),
    path(
        "/salons/<uuid:salon_uid>",
        PublicSalonDetailView.as_view(),
        name="public.salon-detail",
    ),
    path(
        "/booking",
        PublicSalonBookingView.as_view(),
        name="public.salon-booking-list",
    ),
]

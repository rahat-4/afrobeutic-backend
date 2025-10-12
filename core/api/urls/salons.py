from django.urls import path

from ..views.salons import (
    SalonListView,
    SalonDetailView,
    SalonServiceListView,
    SalonServiceDetailView,
)

urlpatterns = [
    path(
        "/<uuid:salon_uid>/services/<uuid:service_uid>",
        SalonServiceDetailView.as_view(),
        name="salon.service-detail",
    ),
    path(
        "/<uuid:salon_uid>/services",
        SalonServiceListView.as_view(),
        name="salon.service-list",
    ),
    path(
        "/<uuid:salon_uid>",
        SalonDetailView.as_view(),
        name="salon.detail",
    ),
    path("", SalonListView.as_view(), name="salon.list"),
]

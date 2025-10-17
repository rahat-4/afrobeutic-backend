from django.urls import path

from ..views.salons import (
    SalonListView,
    SalonDetailView,
    SalonServiceListView,
    SalonServiceDetailView,
    SalonProductListView,
    SalonProductDetailView,
    SalonEmployeeListView,
)

urlpatterns = [
    path(
        "/<uuid:salon_uid>/employees",
        SalonEmployeeListView.as_view(),
        name="salon.employee-list",
    ),
    path(
        "/<uuid:salon_uid>/products/<uuid:product_uid>",
        SalonProductDetailView.as_view(),
        name="salon.product-detail",
    ),
    path(
        "/<uuid:salon_uid>/products",
        SalonProductListView.as_view(),
        name="salon.product-list",
    ),
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

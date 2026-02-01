from django.urls import path

from ..views.filters import (
    FilterEmployeeListView,
    FilterServiceListView,
    FilterProductListView,
)

urlpatterns = [
    path(
        "/<uuid:salon_uid>/employees",
        FilterEmployeeListView.as_view(),
        name="filter-employees",
    ),
    path(
        "/<uuid:salon_uid>/services",
        FilterServiceListView.as_view(),
        name="filter-services",
    ),
    path(
        "/<uuid:salon_uid>/products",
        FilterProductListView.as_view(),
        name="filter-products",
    ),
]

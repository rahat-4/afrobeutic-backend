from django.urls import path

from ..views.customers import CustomerDetailView, CustomerListView, CustomerProfileView

urlpatterns = [
    path(
        "/<uuid:customer_uid>/profile",
        CustomerProfileView.as_view(),
        name="customer.profile",
    ),
    path(
        "/<uuid:customer_uid>",
        CustomerDetailView.as_view(),
        name="customer.detail",
    ),
    path(
        "",
        CustomerListView.as_view(),
        name="customer.list",
    ),
]

from django.urls import path

from ..views.customers import CustomerDetailView, CustomerListView

urlpatterns = [
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

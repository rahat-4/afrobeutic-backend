from django.urls import path

from .views import CategoryListView, LeadCustomerListView

urlpatterns = [
    path("/lead-customer", LeadCustomerListView.as_view(), name="lead-customer.list"),
    path("/categories", CategoryListView.as_view(), name="category-list"),
]

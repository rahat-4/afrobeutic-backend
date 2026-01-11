from django.urls import path

from .views import (
    CategoryListView,
    LeadCustomerListView,
    ServiceCategoryListView,
    ServiceSubCategoryListView,
    ProductCategoryListView,
    ProductSubCategoryListView,
)

urlpatterns = [
    path("/lead-customer", LeadCustomerListView.as_view(), name="lead-customer.list"),
    path(
        "/product-categories/<uuid:product_category_uid>/subcategories",
        ProductSubCategoryListView.as_view(),
        name="product-subcategory-list",
    ),
    path(
        "/product-categories",
        ProductCategoryListView.as_view(),
        name="product-category-list",
    ),
    path(
        "/service-categories/<uuid:service_category_uid>/subcategories",
        ServiceSubCategoryListView.as_view(),
        name="service-subcategory-list",
    ),
    path(
        "/service-categories",
        ServiceCategoryListView.as_view(),
        name="service-category-list",
    ),
    path("/categories", CategoryListView.as_view(), name="category-list"),
]

from django.urls import path

from ..views.filters import FilterPricingPlanListView

urlpatterns = [
    path(
        "/pricing-plans",
        FilterPricingPlanListView.as_view(),
        name="filter-pricing-plans",
    ),
]

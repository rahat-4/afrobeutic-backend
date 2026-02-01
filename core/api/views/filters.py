from rest_framework.generics import ListAPIView
from rest_framework.exceptions import ValidationError

from apps.billing.models import PricingPlan

from ..serializers.filters import FilterPricingPlanSerializer


class FilterPricingPlanListView(ListAPIView):
    queryset = PricingPlan.objects.filter(is_active=True)
    serializer_class = FilterPricingPlanSerializer
    pagination_class = None

    def get_queryset(self):
        account_category = self.request.query_params.get("account_category")
        if not account_category:
            raise ValidationError(
                {"detail": "account_category query parameter is required."}
            )
        return (
            super()
            .get_queryset()
            .filter(account_category=account_category)
            .order_by("price")
        )

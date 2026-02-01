from rest_framework import serializers

from apps.billing.models import PricingPlan


class FilterPricingPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = PricingPlan
        fields = ["uid", "name"]

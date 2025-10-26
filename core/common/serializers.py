from rest_framework import serializers

from apps.salon.models import Customer


class CustomerSlimSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["uid", "name", "phone"]

from rest_framework import serializers

from apps.salon.models import Customer

from common.serializers import BookingSlimSerializer


class CustomerSerializer(serializers.ModelSerializer):
    booking = BookingSlimSerializer(many=True, source="customer_bookings")
    source = serializers.CharField(source="source.name")

    class Meta:
        model = Customer
        fields = [
            "uid",
            "first_name",
            "last_name",
            "email",
            "phone",
            "source",
            "booking",
            "created_at",
            "updated_at",
        ]

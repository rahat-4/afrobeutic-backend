from rest_framework import serializers

from apps.salon.models import Customer

from common.serializers import BookingSlimSerializer


class CustomerSerializer(serializers.ModelSerializer):
    booking = BookingSlimSerializer(many=True, source="customer_bookings")

    class Meta:
        model = Customer
        fields = [
            "uid",
            "name",
            "phone",
            "booking",
            "created_at",
            "updated_at",
        ]

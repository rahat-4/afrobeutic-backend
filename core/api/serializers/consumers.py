from rest_framework import serializers

from apps.salon.models import Booking, Customer

from common.serializers import (
    ChairSlimSerializer,
    EmployeeSlimSerializer,
    ServiceSlimSerializer,
    ProductSlimSerializer,
    MediaSlimSerializer,
)


class CustomerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["uid", "first_name", "last_name", "email", "phone"]


class CustomerBookingSerializer(serializers.ModelSerializer):
    chair = ChairSlimSerializer()
    employee = EmployeeSlimSerializer()
    services = ServiceSlimSerializer(many=True)
    products = ProductSlimSerializer(many=True)
    images = serializers.SerializerMethodField()
    booking_revenue = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = Booking
        fields = [
            "uid",
            "booking_id",
            "booking_date",
            "booking_time",
            "status",
            "notes",
            "booking_duration",
            "cancellation_reason",
            "cancelled_by",
            "completed_at",
            "chair",
            "employee",
            "services",
            "products",
            "images",
            "booking_revenue",
            "created_at",
        ]

    def get_images(self, obj):
        images = obj.booking_images.all()
        return MediaSlimSerializer(images, many=True, context=self.context).data

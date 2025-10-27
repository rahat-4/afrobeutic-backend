from django.contrib.auth import get_user_model

from rest_framework import serializers

from apps.salon.models import (
    Booking,
    Customer,
    Employee,
    Salon,
    Product,
    Service,
    Chair,
)

User = get_user_model()


class UserSlimSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["uid", "first_name", "last_name", "email", "gender"]


class CustomerSlimSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["uid", "name", "phone"]


class EmployeeSlimSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ["uid", "employee_id", "name", "phone", "designation", "image"]


class SalonSlimSerializer(serializers.ModelSerializer):
    class Meta:
        model = Salon
        fields = [
            "uid",
            "name",
            "salon_type",
            "email",
            "phone",
            "city",
            "country",
            "status",
        ]


class ServiceSlimSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = [
            "uid",
            "name",
            "category",
            "price",
            "description",
            "service_duration",
            "available_time_slots",
            "gender_specific",
            "discount_percentage",
        ]


class ProductSlimSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["uid", "name", "category", "price", "description"]


class ChairSlimSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chair
        fields = ["uid", "name", "type"]


class BookingSlimSerializer(serializers.ModelSerializer):
    salon = SalonSlimSerializer()
    employee = EmployeeSlimSerializer()
    services = ServiceSlimSerializer(many=True)
    products = ProductSlimSerializer(many=True)
    chair = ChairSlimSerializer()

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
            "completed_at",
            "cancellation_reason",
            "cancelled_by",
            "salon",
            "chair",
            "employee",
            "services",
            "products",
        ]

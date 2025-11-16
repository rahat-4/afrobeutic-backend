from django.contrib.auth import get_user_model

from rest_framework import serializers

from apps.authentication.models import Account
from apps.salon.models import (
    Booking,
    Customer,
    Employee,
    Salon,
    Product,
    Service,
    Chair,
)

from .models import Media

User = get_user_model()


class UserSlimSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["uid", "first_name", "last_name", "email"]


class CustomerSlimSerializer(serializers.ModelSerializer):
    source = serializers.CharField(source="source.name", read_only=True)

    class Meta:
        model = Customer
        fields = [
            "uid",
            "first_name",
            "last_name",
            "email",
            "source",
            "phone",
            "created_at",
        ]


class EmployeeSlimSerializer(serializers.ModelSerializer):
    designation = serializers.CharField(source="designation.name", read_only=True)

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
    category = serializers.CharField(source="category.name", read_only=True)
    discount_price = serializers.CharField(read_only=True, source="final_price")

    class Meta:
        model = Service
        fields = [
            "uid",
            "name",
            "discount_percentage",
            "price",
            "discount_price",
            "category",
            "description",
            "service_duration",
            "available_time_slots",
            "gender_specific",
        ]


class ProductSlimSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Product
        fields = ["uid", "name", "category", "price", "description"]


class ChairSlimSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source="type.name", read_only=True)

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


class AccountSlimSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source="owner.get_full_name", read_only=True)
    owner_email = serializers.EmailField(source="owner.email", read_only=True)
    role = serializers.SerializerMethodField()

    class Meta:
        model = Account
        fields = ["uid", "name", "owner_name", "owner_email", "role"]

    def get_role(self, obj):
        user = self.context.get("view_user")
        if not user:
            return None

        membership = obj.members.filter(user=user).first()

        return membership.role if membership else None


class MediaSlimSerializer(serializers.ModelSerializer):
    class Meta:
        model = Media
        fields = ["uid", "image", "created_at", "updated_at"]

    def get_image(self, obj):
        request = self.context.get("request")
        if obj.image:
            # Build full absolute URL if request is available
            return (
                request.build_absolute_uri(obj.image.url) if request else obj.image.url
            )
        return None


class LeadSlimSerializer(serializers.ModelSerializer):
    source = serializers.CharField(source="source.name", read_only=True)

    class Meta:
        model = Customer
        fields = [
            "uid",
            "first_name",
            "last_name",
            "email",
            "phone",
            "source",
            "created_at",
            "updated_at",
        ]


class LeadCustomerSerializer(serializers.ModelSerializer):
    source = serializers.CharField(source="source.name", read_only=True)

    class Meta:
        model = Customer
        fields = [
            "uid",
            "first_name",
            "last_name",
            "email",
            "phone",
            "source",
            "created_at",
        ]

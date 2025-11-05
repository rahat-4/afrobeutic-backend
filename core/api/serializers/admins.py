from django.contrib.auth import get_user_model

from rest_framework import serializers

from common.serializers import (
    AccountSlimSerializer,
    UserSlimSerializer,
    EmployeeSlimSerializer,
    CustomerSlimSerializer,
    ChairSlimSerializer,
    ServiceSlimSerializer,
    ProductSlimSerializer,
    MediaSerializer,
)

from apps.authentication.models import Account, AccountMembership
from apps.salon.models import Salon, Service, Product, Employee, Booking

User = get_user_model()


class AdminUserSerializer(serializers.ModelSerializer):
    accounts = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "uid",
            "avatar",
            "first_name",
            "last_name",
            "email",
            "country",
            "accounts",
        ]

    def get_accounts(self, obj):
        memberships = obj.memberships.select_related("account")
        accounts = [membership.account for membership in memberships]
        context = {**self.context, "view_user": obj}
        return AccountSlimSerializer(accounts, many=True, context=context).data


class UserSlimSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "uid",
            "avatar",
            "first_name",
            "last_name",
            "email",
            "role",
            "country",
        ]

    def get_role(self, obj):
        account = self.context.get("account")

        try:
            role = AccountMembership.objects.get(user=obj, account=account).role
        except AccountMembership.DoesNotExist:
            role = None

        return role


class AdminAccountSerializer(serializers.ModelSerializer):
    users = serializers.SerializerMethodField()

    class Meta:
        model = Account
        fields = [
            "uid",
            "name",
            "created_at",
            "users",
        ]

    def get_users(self, obj):
        memberships = obj.members.select_related("user").ordered_by_role()
        users = [membership.user for membership in memberships]

        context = {**self.context, "account": obj}
        return UserSlimSerializer(users, many=True, context=context).data


class AdminSalonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Salon
        fields = [
            "uid",
            "logo",
            "name",
            "salon_type",
            "email",
            "phone",
            "website",
            "street",
            "city",
            "postal_code",
            "country",
            "address",
            "status",
            "created_at",
        ]


class AdminServiceSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source="category.name", read_only=True)
    assign_employees = serializers.SerializerMethodField()

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
            "assign_employees",
            "created_at",
        ]

    def get_assign_employees(self, obj):
        employees = obj.assign_employees.all()
        return EmployeeSlimSerializer(employees, many=True).data


class AdminProductSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Product
        fields = [
            "uid",
            "name",
            "category",
            "price",
            "description",
            "created_at",
        ]


class AdminEmployeeSerializer(serializers.ModelSerializer):
    designation = serializers.CharField(source="designation.name", read_only=True)

    class Meta:
        model = Employee
        fields = [
            "uid",
            "employee_id",
            "name",
            "phone",
            "designation",
            "image",
            "created_at",
        ]


class AdminBookingSerializer(serializers.ModelSerializer):
    customer = CustomerSlimSerializer()
    chair = ChairSlimSerializer()
    employee = EmployeeSlimSerializer()
    services = ServiceSlimSerializer(many=True)
    products = ProductSlimSerializer(many=True)

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
            "customer",
            "chair",
            "employee",
            "services",
            "products",
            "created_at",
        ]


class AdminLookBookSerializer(serializers.ModelSerializer):
    customer = CustomerSlimSerializer()
    images = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            "uid",
            "booking_id",
            "customer",
            "completed_at",
            "images",
            "created_at",
            "updated_at",
        ]

    def get_images(self, obj):
        images = obj.booking_images.all()
        return MediaSerializer(images, many=True, context=self.context).data

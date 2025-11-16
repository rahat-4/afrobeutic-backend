from django.contrib.auth import get_user_model
from django.db import transaction

from rest_framework import serializers

from common.models import Media
from common.serializers import (
    AccountSlimSerializer,
    UserSlimSerializer,
    EmployeeSlimSerializer,
    CustomerSlimSerializer,
    ChairSlimSerializer,
    ServiceSlimSerializer,
    ProductSlimSerializer,
    MediaSlimSerializer,
)

from apps.authentication.models import Account, AccountMembership
from apps.salon.models import Salon, Service, Product, Employee, Booking
from apps.support.models import SupportTicket

User = get_user_model()


class AdminRegistrationSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(choices=["ADMIN", "STAFF"], write_only=True)
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = [
            "uid",
            "first_name",
            "last_name",
            "email",
            "country",
            "role",
            "password",
            "confirm_password",
        ]

    def validate(self, attrs):
        errors = {}

        if attrs.get("password") != attrs.get("confirm_password"):
            errors["confirm_password"] = "Passwords do not match."
        if User.objects.filter(email=attrs.get("email")).exists():
            errors["email"] = "Email already exists."

        if errors:
            raise serializers.ValidationError(errors)

        return attrs

    def create(self, validated_data):
        with transaction.atomic():
            role = validated_data.pop("role")
            validated_data.pop("confirm_password", None)
            password = validated_data.pop("password")

            user = User(**validated_data)
            user.is_active = False  # User must verify email to activate account
            if role == "ADMIN":
                user.is_admin = True
                user.is_staff = True
            elif role == "STAFF":
                user.is_staff = True

            user.set_password(password)
            user.save()

            return user


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
    images = serializers.SerializerMethodField()

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
            "images",
            "created_at",
        ]

    def get_images(self, obj):
        images = obj.booking_images.all()
        return MediaSlimSerializer(images, many=True, context=self.context).data


class AdminManagementSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "uid",
            "avatar",
            "first_name",
            "last_name",
            "email",
            "country",
            "role",
            "last_login",
        ]

    def get_role(self, obj):
        if obj.is_admin and obj.is_staff:
            return "Admin"
        else:
            return "Staff"


class AdminAccountEnquirySerializer(serializers.ModelSerializer):
    images = MediaSlimSerializer(
        many=True, read_only=True, source="support_ticket_images"
    )

    class Meta:
        model = SupportTicket
        fields = [
            "uid",
            "level",
            "topic",
            "subject",
            "queries",
            "status",
            "images",
            "created_at",
        ]

        read_only_fields = [
            "uid",
            "level",
            "topic",
            "subject",
            "queries",
            "images",
            "created_at",
        ]

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
    PricingPlanSlimSerializer,
)

from apps.authentication.models import Account, AccountMembership
from apps.salon.models import Salon, Service, Product, Employee, Booking, Customer
from apps.support.models import SupportTicket
from apps.billing.models import PricingPlan, Subscription

User = get_user_model()


class AdminRegistrationSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(
        choices=["MANAGEMENT_ADMIN", "MANAGEMENT_STAFF"], write_only=True
    )
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
            if role == "MANAGEMENT_ADMIN":
                user.is_admin = True
                user.is_staff = True
            elif role == "MANAGEMENT_STAFF":
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
            "salon_category",
            "is_provide_hair_styles",
            "hair_service_types",
            "is_provide_bridal_makeup_services",
            "bridal_makeup_service_types",
            "salon_type",
            "additional_service_types",
            "formatted_address",
            "google_place_id",
            "latitude",
            "longitude",
            "city",
            "postal_code",
            "country",
            "phone_number_one",
            "phone_number_two",
            "email",
            "facebook",
            "instagram",
            "youtube",
            "status",
            "opening_hours",
            "created_at",
            "updated_at",
        ]


class AdminCustomerSerializer(serializers.ModelSerializer):
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
            "customer",
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


class AdminManagementSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(
        choices=["MANAGEMENT_ADMIN", "MANAGEMENT_STAFF"], write_only=True
    )

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
        read_only_fields = ["uid", "email", "last_login"]

    def management_role(self, obj):
        if obj.is_admin and obj.is_staff:
            return "MANAGEMENT_ADMIN"
        else:
            return "MANAGEMENT_STAFF"

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["role"] = self.management_role(instance)
        return representation

    def update(self, instance, validated_data):
        with transaction.atomic():
            role = validated_data.pop("role")
            instance = super().update(instance, validated_data)

            if role == "MANAGEMENT_ADMIN":
                instance.is_admin = True
                instance.is_staff = True
            elif role == "MANAGEMENT_STAFF":
                instance.is_staff = True
                instance.is_admin = False
            instance.save()

            return instance


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


class AdminPricingPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = PricingPlan
        fields = [
            "uid",
            "account_category",
            "name",
            "price",
            "salon_limit",
            "whatsapp_chatbot_limit",
            "whatsapp_messages_per_chatbot",
            "has_broadcasting",
            "broadcasting_message_limit",
            "is_active",
            "description",
        ]

    def validate_name(self, value):
        """
        - Normalize name (strip + title)
        - Case-insensitive uniqueness
        - Safe for both create & update
        """
        normalized_value = value.strip().title()

        qs = PricingPlan.objects.filter(name__iexact=normalized_value)

        # Exclude current instance on update
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise serializers.ValidationError(
                "A pricing plan with this name already exists."
            )

        return normalized_value


class AdminSubscriptionGetSerializer(serializers.ModelSerializer):
    pricing_plan = PricingPlanSlimSerializer(read_only=True)
    account = AccountSlimSerializer(read_only=True)

    class Meta:
        model = Subscription
        fields = [
            "uid",
            "status",
            "start_date",
            "end_date",
            "next_billing_date",
            "auto_renew",
            "cancelled_at",
            "notes",
            "pricing_plan",
            "account",
            "created_at",
        ]


class AdminSubscriptionPostSerializer(serializers.ModelSerializer):
    account = serializers.SlugRelatedField(
        slug_field="uid",
        queryset=Account.objects.all(),
    )
    pricing_plan = serializers.SlugRelatedField(
        slug_field="uid",
        queryset=PricingPlan.objects.all(),
    )

    class Meta:
        model = Subscription
        fields = [
            "uid",
            "status",
            "start_date",
            "end_date",
            "next_billing_date",
            "auto_renew",
            "cancelled_at",
            "notes",
            "pricing_plan",
            "account",
            "created_at",
        ]

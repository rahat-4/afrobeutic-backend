from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from rest_framework import serializers

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.authentication.models import Account, AccountMembership, AccountInvitation
from apps.authentication.choices import AccountMembershipRole
from apps.billing.models import Subscription, PricingPlan
from apps.billing.choices import SubscriptionStatus

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)
    account_type = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "uid",
            "first_name",
            "last_name",
            "email",
            "country",
            "account_type",
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
            validated_data.pop("confirm_password", None)
            password = validated_data.pop("password")
            account_type = validated_data.pop("account_type")

            user = User(**validated_data)
            user.is_active = False  # User must verify email to activate account
            user.set_password(password)
            user.save()

            account = Account.objects.create(
                name=f"{user.first_name}'s Account",
                owner=user,
                account_type=account_type,
            )

            AccountMembership.objects.create(
                user=user,
                account=account,
                role=AccountMembershipRole.OWNER,
                is_owner=True,
            )

            # One month free trial setup
            pricing_plan = PricingPlan.objects.filter(
                account_category=account_type, name="Free"
            ).first()

            Subscription.objects.create(
                status=SubscriptionStatus.PENDING,
                start_date=timezone.now(),
                end_date=timezone.now() + timezone.timedelta(days=30),
                next_billing_date=timezone.now() + timezone.timedelta(days=30),
                auto_renew=False,
                pricing_plan=pricing_plan,
                account=account,
            )

            return user


class AccountSerializer(serializers.ModelSerializer):
    uid = serializers.CharField(source="account.uid", read_only=True)
    name = serializers.CharField(source="account.name", read_only=True)
    owner_email = serializers.CharField(source="account.owner.email", read_only=True)

    class Meta:
        model = AccountMembership
        fields = ["uid", "name", "owner_email", "role"]


class AccountSlimSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ["uid", "name", "account_type", "created_at"]
        read_only_fields = ["uid", "account_type", "created_at"]


class MeSerializer(serializers.ModelSerializer):
    account = serializers.CharField(write_only=True, required=False)
    is_salon_limit_reached = serializers.SerializerMethodField()
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
            "account",
            "is_salon_limit_reached",
        ]
        read_only_fields = ["uid", "email", "role"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = self.context.get("request")
        if not request:
            return

        user = request.user

        # 🔥 Remove account field for admin or staff
        if user.is_admin or user.is_staff:
            self.fields.pop("account", None)

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        request = self.context.get("request")
        user = request.user
        if not (user.is_admin or user.is_staff):
            account = request.account
            rep["account"] = AccountSlimSerializer(account).data

        return rep

    def get_is_salon_limit_reached(self, obj):
        request = self.context.get("request")
        user = request.user

        if user.is_admin or user.is_staff:
            return False

        account = request.account
        subscription = getattr(account, "account_subscription", None)

        if subscription:
            salon_limit = subscription.pricing_plan.salon_limit
            current_salon_count = account.account_salons.count()
            return current_salon_count >= salon_limit

        return False

    def get_role(self, obj):
        user = self.context.get("request").user

        if user.is_admin and user.is_staff:
            role = "MANAGEMENT_ADMIN"
        elif user.is_staff:
            role = "MANAGEMENT_STAFF"
        else:
            account = self.context.get("request").account
            try:
                role = AccountMembership.objects.get(user=obj, account=account).role
            except AccountMembership.DoesNotExist:
                role = None

        return role

    def update(self, instance, validated_data):
        request = self.context.get("request")
        account_data = validated_data.pop("account", None)

        # Update user fields normally
        instance = super().update(instance, validated_data)

        # Handle account name update
        if account_data:
            account = request.account

            try:
                membership = AccountMembership.objects.get(
                    user=instance, account=account
                )
            except AccountMembership.DoesNotExist:
                raise serializers.ValidationError("No membership found.")

            if membership.role != "OWNER":
                raise serializers.ValidationError(
                    {"account": "Only OWNER can update account name."}
                )

            account_instance = account
            account_instance.name = account_data
            account_instance.save()

        return instance


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        if self.user.is_staff:
            pass
        else:
            # Add custom data to the response
            account = self.user.memberships.filter(is_owner=True).first().account
            if account:
                data["account_id"] = str(account.uid)
            else:
                data["account_id"] = None

        return data

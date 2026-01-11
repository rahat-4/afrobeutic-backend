from django.contrib.auth import get_user_model
from django.db import transaction

from rest_framework import serializers

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.authentication.models import Account, AccountMembership, AccountInvitation
from apps.authentication.choices import AccountMembershipRole

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)
    account_timezone = serializers.CharField(write_only=True)
    account_type = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "uid",
            "first_name",
            "last_name",
            "email",
            "country",
            "account_timezone",
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
            account_timezone = validated_data.pop("account_timezone")

            user = User(**validated_data)
            user.is_active = False  # User must verify email to activate account
            user.set_password(password)
            user.save()

            account = Account.objects.create(
                name=f"{user.first_name}'s Account",
                owner=user,
                account_type=account_type,
                account_timezone=account_timezone,
            )

            AccountMembership.objects.create(
                user=user,
                account=account,
                role=AccountMembershipRole.OWNER,
                is_owner=True,
            )

            return user


class AccountSerializer(serializers.ModelSerializer):
    uid = serializers.CharField(source="account.uid", read_only=True)
    name = serializers.CharField(source="account.name", read_only=True)
    owner_email = serializers.CharField(source="account.owner.email", read_only=True)

    class Meta:
        model = AccountMembership
        fields = ["uid", "name", "owner_email", "role"]


class MeSerializer(serializers.ModelSerializer):
    account_type = serializers.CharField(
        source="memberships.first.account.account_type", read_only=True
    )
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
            "account_type",
        ]
        read_only_fields = ["uid", "email", "role"]

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

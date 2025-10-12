from django.contrib.auth import get_user_model
from django.db import transaction

from rest_framework import serializers

from apps.authentication.models import Account, AccountMembership, AccountInvitation
from apps.authentication.choices import AccountMembershipRole

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
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
            user = User(**validated_data)
            user.is_active = False  # User must verify email to activate account
            user.set_password(password)
            user.save()

            account = Account.objects.create(
                name=f"{user.first_name}'s Account", owner=user
            )

            AccountMembership.objects.create(
                user=user, account=account, role=AccountMembershipRole.OWNER
            )

            return user


class AccountInvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountInvitation
        fields = ["email", "role"]
        extra_kwargs = {
            "email": {"required": True},
            "role": {"required": True},
        }

    def validate_email(self, value):
        request = self.context.get("request")
        if request and request.user.email.lower() == value.lower():
            raise serializers.ValidationError("You cannot invite yourself.")

        # Check for existing unaccepted invitation
        account_invitation = AccountInvitation.objects.filter(
            email=value, is_accepted=False
        ).first()

        if account_invitation:
            if account_invitation.is_expired():
                account_invitation.delete()
            else:
                raise serializers.ValidationError(
                    "An invitation has already been sent to this email."
                )
        return value


class AccountSerializer(serializers.ModelSerializer):
    uid = serializers.CharField(source="account.uid", read_only=True)
    name = serializers.CharField(source="account.name", read_only=True)
    owner_email = serializers.CharField(source="account.owner.email", read_only=True)

    class Meta:
        model = AccountMembership
        fields = ["uid", "name", "owner_email", "role"]


class MeSerializer(serializers.ModelSerializer):
    accounts = AccountSerializer(source="memberships", many=True, read_only=True)

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
        read_only_fields = ["uid", "email"]

from django.contrib.auth import get_user_model
from django.db import transaction

from rest_framework import serializers

from apps.authentication.choices import AccountMembershipRole
from apps.authentication.models import Account, AccountInvitation, AccountMembership


User = get_user_model()


class AccountMemberSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(source="user.avatar", read_only=True)
    name = serializers.CharField(source="user.get_full_name", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = AccountMembership
        fields = ["uid", "avatar", "name", "email", "role", "status"]
        read_only_fields = ["uid", "name", "email"]


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


class AccountAccessSerializer(serializers.ModelSerializer):
    owner_name = serializers.SerializerMethodField()
    owner_email = serializers.EmailField(source="owner.email", read_only=True)
    role = serializers.SerializerMethodField()

    class Meta:
        model = Account
        fields = ["uid", "name", "owner_name", "owner_email", "role"]

    def get_owner_name(self, obj):
        return f"{obj.owner.first_name} {obj.owner.last_name}"

    def get_role(self, obj):
        user = self.context.get("request").user
        membership = obj.members.filter(user=user).first()
        return membership.role if membership else None

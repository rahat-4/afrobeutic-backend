from django.contrib.auth import get_user_model

from rest_framework import serializers

from apps.authentication.models import Account, AccountMembership

from common.serializers import AccountSlimSerializer, UserSlimSerializer

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
            "owner",
            "created_at",
            "users",
        ]

    def get_users(self, obj):
        memberships = obj.members.select_related("user").ordered_by_role()
        users = [membership.user for membership in memberships]

        context = {**self.context, "account": obj}
        return UserSlimSerializer(users, many=True, context=context).data

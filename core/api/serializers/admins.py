from django.contrib.auth import get_user_model

from rest_framework import serializers

from common.serializers import AccountSlimSerializer

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

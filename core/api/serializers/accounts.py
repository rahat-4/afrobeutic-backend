from rest_framework import serializers

from apps.authentication.models import Account


class AccountSerializer(serializers.ModelSerializer):
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

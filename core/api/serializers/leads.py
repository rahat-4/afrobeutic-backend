from django.db import transaction
from rest_framework import serializers

from apps.salon.models import Customer, Salon

from common.choices import CategoryType
from common.utils import get_or_create_category
from common.serializers import SalonSlimSerializer


class AccountLeadSerializer(serializers.ModelSerializer):
    salon = serializers.SlugRelatedField(
        slug_field="uid", write_only=True, queryset=Salon.objects.all()
    )
    source = serializers.CharField(write_only=True)

    class Meta:
        model = Customer
        fields = [
            "uid",
            "first_name",
            "last_name",
            "email",
            "phone",
            "salon",
            "source",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        phone = attrs.get("phone")
        account = self.context["request"].account

        errors = {}

        # Check uniqueness of phone
        qs = Customer.objects.filter(account=account, phone=phone)
        if self.instance:
            qs = qs.exclude(uid=self.instance.uid)
        if qs.exists():
            errors["phone"] = ["Lead with this phone already exists."]

        if errors:
            raise serializers.ValidationError(errors)

        return attrs

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["salon"] = (
            SalonSlimSerializer(instance.salon).data if instance.salon else None
        )

        rep["source"] = instance.source.name
        return rep

    def create(self, validated_data):
        account = self.context["request"].account
        source = validated_data.pop("source")
        salon = validated_data.pop("salon")

        with transaction.atomic():
            # Handle category
            source = get_or_create_category(
                source, account, CategoryType.CUSTOMER_SOURCE
            )
            validated_data["source"] = source
            lead = Customer.objects.create(**validated_data, salon=salon)

            return lead

    def update(self, instance, validated_data):
        account = self.context["request"].account
        source = validated_data.pop("source", None)

        with transaction.atomic():
            # Handle category
            if source:
                source = get_or_create_category(
                    source, account, CategoryType.CUSTOMER_SOURCE
                )
                instance.source = source

            # Update lead fields
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            return instance

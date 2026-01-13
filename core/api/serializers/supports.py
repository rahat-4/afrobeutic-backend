from django.db.models import Q
from django.db import transaction

from rest_framework import serializers

from apps.authentication.choices import AccountType
from apps.salon.choices import CustomerType
from apps.support.models import (
    SupportTicket,
    AccountSupportTicket,
    Salon,
    Customer,
)

from common.choices import CategoryType
from common.models import Media
from common.serializers import (
    MediaSlimSerializer,
    SalonSlimSerializer,
    CustomerSlimSerializer,
)
from common.utils import get_or_create_category


class AccountEnquirySerializer(serializers.ModelSerializer):
    images = MediaSlimSerializer(
        many=True, read_only=True, source="support_ticket_images"
    )
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(), write_only=True, required=False
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
            "uploaded_images",
            "created_at",
        ]

    def validate_uploaded_images(self, value):
        """
        Ensure no more than 3 images are uploaded.
        """
        if len(value) > 3:
            raise serializers.ValidationError("You can upload a maximum of 3 images.")
        return value

    def create(self, validated_data):
        uploaded_images = validated_data.pop("uploaded_images", [])
        support_ticket = SupportTicket.objects.create(**validated_data)

        for image in uploaded_images:
            Media.objects.create(support_ticket=support_ticket, image=image)

        return support_ticket


class CustomerEnquirySerializer(serializers.ModelSerializer):
    salon = serializers.SlugRelatedField(
        slug_field="uid",
        write_only=True,
        queryset=Salon.objects.all(),
        allow_null=True,
        required=False,
    )
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True)
    phone = serializers.CharField(write_only=True)
    source = serializers.CharField(write_only=True)
    lead = CustomerSlimSerializer(source="customer", read_only=True)

    class Meta:
        model = AccountSupportTicket
        fields = [
            "uid",
            "first_name",
            "last_name",
            "email",
            "phone",
            "source",
            "type",
            "summary",
            "status",
            "lead",
            "salon",
            "created_at",
            "updated_at",
        ]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["salon"] = (
            SalonSlimSerializer(instance.salon).data if instance.salon else None
        )

        return representation

    def validate(self, attrs):
        phone = attrs.get("phone")
        account = self.context["request"].account
        errors = {}

        if account.account_type == AccountType.SALON_SHOP:
            salon = attrs.get("salon")
            if not salon:
                raise serializers.ValidationError({"salon": ["Salon is required."]})

        if self.instance:
            allowed_fields = {"status", "type", "summary"}

            for field in attrs.keys():
                if field not in allowed_fields:
                    raise serializers.ValidationError(
                        {field: "This field cannot be updated."}
                    )

        if not phone and self.instance:
            customer = getattr(self.instance, "customer", None)

            phone = getattr(customer, "phone", None)

        if not phone:
            raise serializers.ValidationError({"phone": ["Phone must be provided."]})

        return attrs

    def create(self, validated_data):
        phone = validated_data.pop("phone", None)
        first_name = validated_data.pop("first_name")
        last_name = validated_data.pop("last_name")
        email = validated_data.pop("email", None)
        source = validated_data.pop("source")

        account = self.context["request"].account

        salon = None

        if account.account_type == AccountType.INDIVIDUAL_STYLIST:
            salon = Salon.objects.filter(account=account).first()
        else:
            salon = validated_data.pop("salon")

        with transaction.atomic():

            source = get_or_create_category(
                source, salon.account, category_type=CategoryType.CUSTOMER_SOURCE
            )

            customer, _ = Customer.objects.get_or_create(
                account=salon.account,
                phone=phone,
                defaults={
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": email,
                    "source": source,
                    "salon": salon,
                },
            )

            ticket = AccountSupportTicket.objects.create(
                customer=customer,
                salon=salon,
                **validated_data,
            )

            return ticket

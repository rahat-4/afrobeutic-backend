from django.db.models import Q
from django.db import transaction

from rest_framework import serializers

from apps.support.models import (
    SupportTicket,
    AccountSupportTicket,
    Salon,
    Lead,
    Customer,
)

from common.choices import CategoryType
from common.models import Media
from common.serializers import (
    MediaSlimSerializer,
    SalonSlimSerializer,
    LeadSlimSerializer,
    CustomerSlimSerializer,
)
from common.utils import get_or_create_category


class SupportTicketSerializer(serializers.ModelSerializer):
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


class AccountSupportTicketSerializer(serializers.ModelSerializer):
    salon = serializers.SlugRelatedField(
        slug_field="uid", write_only=True, queryset=Salon.objects.all()
    )
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True)
    phone = serializers.CharField(write_only=True, required=False, allow_blank=True)
    whatsapp = serializers.CharField(write_only=True, required=False, allow_blank=True)
    source = serializers.CharField(write_only=True)

    class Meta:
        model = AccountSupportTicket
        fields = [
            "uid",
            "first_name",
            "last_name",
            "email",
            "phone",
            "whatsapp",
            "source",
            "type",
            "summary",
            "status",
            "lead",
            "customer",
            "salon",
            "created_at",
            "updated_at",
        ]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["salon"] = (
            SalonSlimSerializer(instance.salon).data if instance.salon else None
        )
        representation["lead"] = (
            LeadSlimSerializer(instance.lead).data if instance.lead else None
        )
        representation["customer"] = (
            CustomerSlimSerializer(instance.customer).data
            if instance.customer
            else None
        )

        return representation

    def validate(self, attrs):
        phone = attrs.get("phone")
        whatsapp = attrs.get("whatsapp")

        if not phone and not whatsapp and self.instance:
            lead = getattr(self.instance, "lead", None)
            customer = getattr(self.instance, "customer", None)

            phone = getattr(customer, "phone", None) or getattr(lead, "phone", None)
            whatsapp = getattr(customer, "whatsapp", None) or getattr(
                lead, "whatsapp", None
            )

        if not phone and not whatsapp:
            raise serializers.ValidationError(
                {"non_field_errors": ["Either phone or whatsapp must be provided."]}
            )

        return attrs

    def create(self, validated_data):
        phone = validated_data.pop("phone", None)
        whatsapp = validated_data.pop("whatsapp", None)
        first_name = validated_data.pop("first_name")
        last_name = validated_data.pop("last_name")
        email = validated_data.pop("email")
        source = validated_data.pop("source")
        salon = validated_data["salon"]

        with transaction.atomic():
            customer = None
            lead = None

            if phone or whatsapp:
                customer = Customer.objects.filter(
                    account=salon.account, phone=phone
                ).first()

                if not customer:
                    lead = Lead.objects.filter(
                        Q(account=salon.account, salon=salon, phone=phone)
                        | Q(account=salon.account, salon=salon, whatsapp=whatsapp)
                    ).first()

            if not customer and not lead:
                source = get_or_create_category(
                    source, salon.account, category_type=CategoryType.LEAD_SOURCE
                )
                lead = Lead.objects.create(
                    account=salon.account,
                    salon=salon,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    phone=phone,
                    whatsapp=whatsapp,
                    source=source,
                )

            ticket = AccountSupportTicket.objects.create(
                lead=lead,
                customer=customer,
                **validated_data,
            )

            return ticket

from decimal import Decimal
from datetime import timedelta

from django.db import transaction
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from apps.salon.models import Booking, Customer, Salon, Product, Service, SalonMedia
from apps.salon.choices import BookingStatus, SalonStatus


from common.choices import CategoryType
from common.serializers import MediaSlimSerializer
from common.utils import get_or_create_category


class CustomerProfileSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source="type", read_only=True)

    class Meta:
        model = Customer
        fields = ["uid", "first_name", "last_name", "email", "phone", "role"]


class CustomerSlimSerializer(serializers.ModelSerializer):

    class Meta:
        model = Customer
        fields = [
            "uid",
            "first_name",
            "last_name",
            "email",
            "phone",
            "source",
            "created_at",
            "updated_at",
        ]

        extra_kwargs = {
            "source": {"required": False, "allow_null": True},
        }

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["source"] = instance.source.name if instance.source else None
        return representation


class BookingImageSlimSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalonMedia
        fields = ["uid", "image", "created_at", "updated_at"]


class BookingServicesSlimSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = [
            "uid",
            "name",
            "category",
            "price",
            "description",
            "service_duration",
            "created_at",
            "updated_at",
        ]


class BookingProductsSlimSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "uid",
            "name",
            "category",
            "price",
            "description",
            "created_at",
            "updated_at",
        ]


class CustomerBookingSerializer(serializers.ModelSerializer):
    salon = serializers.SlugRelatedField(
        queryset=Salon.objects.filter(status=SalonStatus.ACTIVE), slug_field="uid"
    )
    services = serializers.SlugRelatedField(
        queryset=Service.objects.all(),
        many=True,
        slug_field="uid",
        required=False,
        allow_null=True,
    )
    products = serializers.SlugRelatedField(
        queryset=Product.objects.all(),
        many=True,
        slug_field="uid",
        required=False,
        allow_null=True,
    )
    total_products = serializers.SerializerMethodField()
    total_products_price = serializers.SerializerMethodField()
    total_services = serializers.SerializerMethodField()
    total_services_price = serializers.SerializerMethodField()
    services_discount_price = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    final_price = serializers.SerializerMethodField()
    images = MediaSlimSerializer(source="salonmedia_set", many=True, read_only=True)

    def get_total_products(self, obj):
        return obj.products.count()

    def get_total_products_price(self, obj):
        return sum(p.price for p in obj.products.all())

    def get_total_services(self, obj):
        return obj.services.count()

    def get_total_services_price(self, obj):
        return sum(s.price for s in obj.services.all())

    def get_services_discount_price(self, obj):
        return sum(s.final_price() for s in obj.services.all())

    def get_total_price(self, obj):
        total_services_price = sum(s.price for s in obj.services.all())
        total_products_price = sum(p.price for p in obj.products.all())
        return total_services_price + total_products_price

    def get_final_price(self, obj):
        final_services_price = sum(
            (Decimal(s.final_price()) for s in obj.services.all()), Decimal("0.00")
        )

        total_products_price = sum(
            (p.price for p in obj.products.all()), Decimal("0.00")
        )

        tips_amount = obj.tips_amount or Decimal("0.00")

        return final_services_price + total_products_price + tips_amount

    def to_representation(self, instance):
        rep = super().to_representation(instance)

        rep["salon"] = {
            "uid": instance.salon.uid,
            "name": instance.salon.name,
        }
        rep["services"] = BookingServicesSlimSerializer(
            instance.services.all(), many=True
        ).data

        rep["products"] = BookingProductsSlimSerializer(
            instance.products.all(), many=True
        ).data

        return rep

    class Meta:
        model = Booking
        fields = [
            "uid",
            "salon",
            "booking_id",
            "booking_date",
            "booking_time",
            "status",
            "booking_duration",
            "cancellation_reason",
            "completed_at",
            "notes",
            "services",
            "products",
            "total_services",
            "total_services_price",
            "total_products",
            "total_products_price",
            "services_discount_price",
            "total_price",
            "final_price",
            "images",
            "tips_amount",
            "payment_type",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "status",
            "booking_duration",
            "booking_id",
            "cancelled_by",
            "completed_at",
            "images",
        ]

    def create(self, validated_data):
        salon = validated_data.pop("salon")
        services = validated_data.pop("services", [])
        products = validated_data.pop("products", [])

        with transaction.atomic():
            total_duration = sum(
                (service.service_duration for service in services), timedelta()
            )
            validated_data["booking_duration"] = total_duration

            booking = Booking.objects.create(
                **validated_data, salon=salon, account=salon.account
            )
            booking.services.set(services)
            if products:
                booking.products.set(products)

            return booking

    def update(self, instance, validated_data):
        services = validated_data.pop("services", None)
        products = validated_data.pop("products", None)

        with transaction.atomic():
            # Update booking fields
            for attr, value in validated_data.items():
                setattr(instance, attr, value)

            # Update services
            if services is not None:
                instance.services.set(services)
                total_duration = sum(
                    (service.service_duration for service in services), timedelta()
                )
                instance.booking_duration = total_duration

            # Update products
            if products is not None:
                instance.products.set(products)

            instance.save()

            return instance

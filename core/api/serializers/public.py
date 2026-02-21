from datetime import timedelta

from django.db import transaction
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from common.choices import CategoryType
from common.serializers import OpeningHoursSlimSerializer
from common.utils import get_or_create_category

from apps.salon.models import Customer, Salon, Booking, Service, Product, SalonMedia
from apps.salon.choices import BookingStatus, CustomerType, SalonStatus


class PublicSalonSerializer(serializers.ModelSerializer):
    opening_hours = OpeningHoursSlimSerializer(many=True, read_only=True)

    class Meta:
        model = Salon
        fields = [
            "uid",
            "logo",
            "name",
            "salon_category",
            "is_provide_hair_styles",
            "hair_service_types",
            "is_provide_bridal_makeup_services",
            "bridal_makeup_service_types",
            "salon_type",
            "additional_service_types",
            "formatted_address",
            "google_place_id",
            "latitude",
            "longitude",
            "city",
            "postal_code",
            "country",
            "phone_number_one",
            "phone_number_two",
            "email",
            "facebook",
            "instagram",
            "youtube",
            "status",
            "about_salon",
            "professional_career_details",
            "opening_hours",
            "created_at",
            "updated_at",
        ]


class PublicCustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone",
        ]
        extra_kwargs = {
            "phone": {"validators": []},
        }


class PublicSalonBookingSerializer(serializers.ModelSerializer):
    customer = PublicCustomerSerializer()
    salon = serializers.SlugRelatedField(
        queryset=Salon.objects.filter(status=SalonStatus.ACTIVE),
        slug_field="uid",
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

    class Meta:
        model = Booking
        fields = [
            "uid",
            "salon",
            "customer",
            "booking_id",
            "booking_date",
            "booking_time",
            "status",
            "notes",
            "booking_duration",
            "services",
            "products",
        ]
        read_only_fields = ["booking_id", "status", "booking_duration"]

    def create(self, validated_data):
        salon = validated_data["salon"]
        account = salon.account
        customer = validated_data.pop("customer")
        services = validated_data.pop("services", [])
        products = validated_data.pop("products", [])

        with transaction.atomic():
            customer_source = customer.get("source", "Booking")

            source = get_or_create_category(
                customer_source, account, category_type=CategoryType.CUSTOMER_SOURCE
            )

            customer_obj, _ = Customer.objects.get_or_create(
                # account=account,
                phone=customer["phone"],
                defaults={
                    "first_name": customer["first_name"],
                    "last_name": customer["last_name"],
                    "email": customer.get("email"),
                    "source": source,
                    "type": CustomerType.CUSTOMER,
                    "salon": validated_data["salon"],
                    "account": account,
                },
            )
            validated_data["customer"] = customer_obj

            total_duration = sum(
                (service.service_duration for service in services), timedelta()
            )
            validated_data["booking_duration"] = total_duration

            booking = Booking.objects.create(**validated_data, account=account)
            booking.services.set(services)
            if products:
                booking.products.set(products)

            return booking

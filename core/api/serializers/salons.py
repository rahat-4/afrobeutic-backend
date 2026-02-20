from datetime import datetime, timedelta, time
from decimal import Decimal

from django.contrib.gis.geos import Point
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.generics import get_object_or_404

from apps.authentication.choices import AccountType
from apps.salon.choices import (
    BookingStatus,
    CustomerType,
    HairServiceType,
    BridalMakeupServiceType,
    AdditionalServiceType,
)
from apps.salon.models import (
    Salon,
    OpeningHours,
    SalonMedia,
    ServiceCategory,
    ServiceSubCategory,
    Service,
    ProductCategory,
    ProductSubCategory,
    Product,
    Chair,
    Employee,
    Customer,
    Booking,
)

from common.choices import CategoryType
from common.serializers import (
    CustomerSlimSerializer,
    EmployeeSlimSerializer,
    ProductSlimSerializer,
    ServiceSlimSerializer,
    MediaSlimSerializer,
)
from common.models import Category
from common.utils import get_or_create_category


class OpeningHoursSerializer(serializers.ModelSerializer):

    class Meta:
        model = OpeningHours
        exclude = ["salon", "created_at", "updated_at"]


class SalonSerializer(serializers.ModelSerializer):
    opening_hours = OpeningHoursSerializer(many=True, required=False)
    hair_service_types = serializers.ListField(
        child=serializers.ChoiceField(choices=HairServiceType.choices), required=False
    )

    bridal_makeup_service_types = serializers.ListField(
        child=serializers.ChoiceField(choices=BridalMakeupServiceType.choices),
        required=False,
    )

    additional_service_types = serializers.ListField(
        child=serializers.ChoiceField(choices=AdditionalServiceType.choices),
        required=False,
    )
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()

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

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["latitude"] = instance.location.y if instance.location else None
        rep["longitude"] = instance.location.x if instance.location else None

        return rep

    def validate(self, attrs):
        opening_hours = attrs.get("opening_hours", [])
        errors = {}
        opening_hours_errors = {}

        account = self.context["request"].account

        subscription = account.account_subscription
        if subscription and subscription.pricing_plan.salon_limit:
            salon_limit = subscription.pricing_plan.salon_limit
            existing_salons_count = Salon.objects.filter(account=account).count()

            if self.instance:
                # If updating an existing salon, exclude it from the count
                existing_salons_count -= 1

            if existing_salons_count >= salon_limit:
                errors["salon_limit"] = [
                    f"Your current subscription plan allows a maximum of {salon_limit} salon(s). Please upgrade your plan to add more salons."
                ]

        for day_data in opening_hours:
            day = day_data.get("day")
            is_closed = day_data.get("is_closed", False)

            opening_time = day_data.get("opening_time")
            closing_time = day_data.get("closing_time")

            day_label = day.capitalize() if day else "Unknown"

            # If salon is closed, times should not be required
            if is_closed:
                continue

            # If salon is open, both times are required
            if not opening_time or not closing_time:
                opening_hours_errors[day_label] = [
                    "Opening time and closing time are required unless the day is marked as closed."
                ]
                continue

            # Opening time must be before closing time
            if opening_time >= closing_time:
                opening_hours_errors[day_label] = [
                    "Opening time must be before closing time."
                ]

        if opening_hours_errors:
            errors["opening_hours"] = opening_hours_errors

        if errors:
            raise serializers.ValidationError(errors)

        return attrs

    def create(self, validated_data):
        with transaction.atomic():
            lat = validated_data.pop("latitude")
            lng = validated_data.pop("longitude")
            opening_hours = validated_data.pop("opening_hours", [])

            validated_data["location"] = Point(lng, lat, srid=4326)

            salon = Salon.objects.create(**validated_data)

            for opening_hour in opening_hours:
                OpeningHours.objects.create(salon=salon, **opening_hour)
            return salon

    def update(self, instance, validated_data):
        with transaction.atomic():
            lat = validated_data.pop("latitude", None)
            lng = validated_data.pop("longitude", None)

            if lat is not None and lng is not None:
                instance.location = Point(lng, lat, srid=4326)

            opening_hours = validated_data.pop("opening_hours", [])

            for attr, value in validated_data.items():
                setattr(instance, attr, value)

            instance.save()

            # Opening Hours
            if opening_hours != []:
                OpeningHours.objects.filter(salon=instance).delete()
                for opening_hour in opening_hours:
                    OpeningHours.objects.create(salon=instance, **opening_hour)
            return instance


class SalonMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalonMedia
        fields = ["uid", "image", "created_at", "updated_at"]


class SalonServiceSerializer(serializers.ModelSerializer):
    images = SalonMediaSerializer(many=True, read_only=True, source="service_images")
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(), write_only=True, required=False
    )
    assign_employees = serializers.SlugRelatedField(
        queryset=Employee.objects.all(),
        many=True,
        slug_field="uid",
        required=False,
    )
    category = serializers.SlugRelatedField(
        queryset=ServiceCategory.objects.all(), slug_field="uid", write_only=True
    )
    sub_category = serializers.SlugRelatedField(
        queryset=ServiceSubCategory.objects.all(),
        slug_field="uid",
        write_only=True,
    )
    discount_price = serializers.CharField(read_only=True, source="final_price")

    class Meta:
        model = Service
        fields = [
            "uid",
            "name",
            "category",
            "sub_category",
            "discount_percentage",
            "price",
            "discount_price",
            "description",
            "images",
            "uploaded_images",
            "service_duration",
            "available_time_slots",
            "gender_specific",
            "assign_employees",
            "created_at",
            "updated_at",
        ]

    def validate(self, data):
        category = data.get("category")
        sub_category = data.get("sub_category")

        if sub_category and sub_category.category != category:
            raise serializers.ValidationError(
                {
                    "sub_category": "Sub-category does not belong to the selected category."
                }
            )

        return data

    def validate_uploaded_images(self, value):
        """
        Ensure no more than 2 images are uploaded.
        """
        if len(value) > 2:
            raise serializers.ValidationError("You can upload a maximum of 2 images.")
        return value

    def to_representation(self, instance):
        rep = super().to_representation(instance)

        rep["assign_employees"] = EmployeeSlimSerializer(
            instance.assign_employees.all(), many=True
        ).data

        rep["category"] = instance.category.name
        rep["sub_category"] = (
            instance.sub_category.name if instance.sub_category else None
        )

        return rep

    def create(self, validated_data):
        uploaded_images = validated_data.pop("uploaded_images", [])
        assign_employees = validated_data.pop("assign_employees", [])
        category = validated_data.pop("category", None)
        sub_category = validated_data.pop("sub_category", None)

        account = self.context["request"].account

        with transaction.atomic():
            service = Service.objects.create(
                category=category, sub_category=sub_category, **validated_data
            )

            if assign_employees:
                service.assign_employees.set(assign_employees)

            for image in uploaded_images:
                SalonMedia.objects.create(service=service, image=image)

            return service

    def update(self, instance, validated_data):
        uploaded_images = validated_data.pop("uploaded_images", None)
        assign_employees = validated_data.pop("assign_employees", None)
        sub_category = validated_data.pop("sub_category", None)
        category = validated_data.pop("category", None)

        with transaction.atomic():
            if category:
                instance.category = category

            if sub_category:
                instance.sub_category = sub_category

            for attr, value in validated_data.items():
                setattr(instance, attr, value)

            instance.save()

            if assign_employees is not None:
                instance.assign_employees.set(assign_employees)

            if uploaded_images is not None:
                instance.service_images.all().delete()
                for image in uploaded_images:
                    SalonMedia.objects.create(service=instance, image=image)

            return instance


class SalonProductSerializer(serializers.ModelSerializer):
    images = SalonMediaSerializer(many=True, read_only=True, source="product_images")
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(), write_only=True, required=False
    )
    category = serializers.SlugRelatedField(
        slug_field="uid",
        queryset=ProductCategory.objects.all(),
        write_only=True,
    )
    sub_category = serializers.SlugRelatedField(
        slug_field="uid",
        queryset=ProductSubCategory.objects.all(),
        write_only=True,
    )

    class Meta:
        model = Product
        fields = [
            "uid",
            "name",
            "category",
            "sub_category",
            "price",
            "description",
            "images",
            "uploaded_images",
            "created_at",
            "updated_at",
        ]

    def validate(self, data):
        category = data.get("category")
        sub_category = data.get("sub_category")

        if sub_category and sub_category.category != category:
            raise serializers.ValidationError(
                {
                    "sub_category": "Sub-category does not belong to the selected category."
                }
            )

        return data

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["category"] = instance.category.name
        rep["sub_category"] = (
            instance.sub_category.name if instance.sub_category else None
        )

        return rep

    def validate_uploaded_images(self, value):
        """
        Ensure no more than 2 images are uploaded.
        """
        if len(value) > 2:
            raise serializers.ValidationError("You can upload a maximum of 2 images.")
        return value

    def create(self, validated_data):
        uploaded_images = validated_data.pop("uploaded_images", [])
        category = validated_data.pop("category")
        sub_category = validated_data.pop("sub_category")

        account = self.context["request"].account

        with transaction.atomic():
            product = Product.objects.create(
                category=category, sub_category=sub_category, **validated_data
            )

            # Create images
            for index, image in enumerate(uploaded_images):
                SalonMedia.objects.create(product=product, image=image)

            return product

    def update(self, instance, validated_data):
        uploaded_images = validated_data.pop("uploaded_images", None)
        category = validated_data.pop("category", None)
        sub_category = validated_data.pop("sub_category", None)
        account = instance.account

        with transaction.atomic():
            # Handle category
            if category:
                instance.category = category
            if sub_category:
                instance.sub_category = sub_category

            # Update product fields
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            # If new images are uploaded, replace old ones
            if uploaded_images is not None:
                # Delete old images
                SalonMedia.objects.filter(product=instance).delete()

                # Create new images
                for index, image in enumerate(uploaded_images):
                    SalonMedia.objects.create(product=instance, image=image)

            return instance


class EmployeeSerializer(serializers.ModelSerializer):
    designation = serializers.CharField(write_only=True)

    class Meta:
        model = Employee
        fields = [
            "uid",
            "employee_id",
            "name",
            "phone",
            "designation",
            "image",
            "created_at",
            "updated_at",
        ]

    def validate_employee_id(self, value):
        """
        Ensure employee_id is unique within the salon.
        """

        account = self.context["request"].account
        salon_uid = self.context["view"].kwargs.get("salon_uid")
        salon = get_object_or_404(Salon, uid=salon_uid, account=account)
        if self.instance:
            # Exclude current instance when checking for uniqueness
            if (
                Employee.objects.filter(
                    account=account, salon=salon, employee_id=value.upper()
                )
                .exclude(uid=self.instance.uid)
                .exists()
            ):
                raise serializers.ValidationError(
                    "Employee ID must be unique within the salon."
                )
        else:
            if Employee.objects.filter(
                account=account, salon=salon, employee_id=value.upper()
            ).exists():
                raise serializers.ValidationError(
                    "Employee ID must be unique within the salon."
                )
        return value

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["designation"] = instance.designation.name
        return rep

    def create(self, validated_data):
        account = self.context["request"].account
        designation_name = validated_data.pop("designation")
        employee_id = validated_data.pop("employee_id").upper()

        with transaction.atomic():
            # Handle category
            designation = get_or_create_category(
                designation_name, account, CategoryType.EMPLOYEE
            )
            validated_data["designation"] = designation
            employee = Employee.objects.create(
                **validated_data, employee_id=employee_id
            )

            return employee

    def update(self, instance, validated_data):
        account = self.context["request"].account
        designation_name = validated_data.pop("designation", None)

        with transaction.atomic():
            # Handle category
            if designation_name:
                designation = get_or_create_category(
                    designation_name, account, CategoryType.EMPLOYEE
                )
                instance.designation = designation

            # Update employee fields
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            return instance


class SalonChairSerializer(serializers.ModelSerializer):
    type = serializers.CharField(write_only=True)

    class Meta:
        model = Chair
        fields = ["uid", "name", "type", "status", "created_at", "updated_at"]

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["type"] = instance.type.name
        return rep

    def create(self, validated_data):
        account = self.context["request"].account
        chair_type = validated_data.pop("type")

        with transaction.atomic():
            # Handle category
            chair_type = get_or_create_category(chair_type, account, CategoryType.CHAIR)
            validated_data["type"] = chair_type
            chair = Chair.objects.create(**validated_data)

            return chair

        with transaction.atomic():
            # Handle category
            chair_type = get_or_create_category(chair_type, account, CategoryType.CHAIR)
            validated_data["type"] = chair_type
            chair = Chair.objects.create(**validated_data)

            return chair

    def update(self, instance, validated_data):
        account = self.context["request"].account
        chair_type = validated_data.pop("type", None)

        with transaction.atomic():
            # Handle category
            if chair_type:
                chair_type = get_or_create_category(
                    chair_type, account, CategoryType.CHAIR
                )
                instance.type = chair_type

            # Update chair fields
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            return instance


class SalonCustomerSlimSerializer(serializers.ModelSerializer):

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


class SalonBookingSerializer(serializers.ModelSerializer):
    customer = SalonCustomerSlimSerializer()
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
    images = serializers.ListField(
        child=serializers.ImageField(), required=False, write_only=True
    )

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
        images_qs = SalonMedia.objects.filter(booking=instance)

        rep["services"] = BookingServicesSlimSerializer(
            instance.services.all(), many=True
        ).data

        rep["products"] = BookingProductsSlimSerializer(
            instance.products.all(), many=True
        ).data

        rep["images"] = MediaSlimSerializer(
            images_qs, many=True, context=self.context
        ).data

        return rep

    class Meta:
        model = Booking
        fields = [
            "uid",
            "customer",
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
        read_only_fields = ["booking_duration", "booking_id", "cancelled_by"]

    def validate(self, attrs):
        images = attrs.get("images", [])
        status = attrs.get("status")
        cancellation_reason = attrs.get("cancellation_reason", None)
        errors = {}

        if len(images) > 3:
            errors["images"] = [_("A maximum of three images can be uploaded.")]

        if status == BookingStatus.CANCELLED and not cancellation_reason:
            errors["cancellation_reason"] = [
                _("Cancellation reason is required when booking is cancelled.")
            ]

        if errors:
            raise serializers.ValidationError(errors)
        return attrs

    def create(self, validated_data):
        customer = validated_data.pop("customer")
        services = validated_data.pop("services", [])
        products = validated_data.pop("products", [])
        account = self.context["request"].account

        with transaction.atomic():
            customer_source = customer.get("source", "Booking")

            source = get_or_create_category(
                customer_source, account, category_type=CategoryType.CUSTOMER_SOURCE
            )

            customer_obj, _ = Customer.objects.get_or_create(
                account=validated_data["account"],
                phone=customer["phone"],
                defaults={
                    "first_name": customer["first_name"],
                    "last_name": customer["last_name"],
                    "email": customer.get("email"),
                    "source": source,
                    "type": CustomerType.CUSTOMER,
                    "salon": validated_data["salon"],
                },
            )
            validated_data["customer"] = customer_obj

            total_duration = sum(
                (service.service_duration for service in services), timedelta()
            )
            validated_data["booking_duration"] = total_duration

            booking = Booking.objects.create(**validated_data)
            booking.services.set(services)
            if products:
                booking.products.set(products)

            return booking

    def update(self, instance, validated_data):
        customer_data = validated_data.pop("customer", None)
        services = validated_data.pop("services", None)
        products = validated_data.pop("products", None)
        images = validated_data.pop("images", [])
        status = validated_data.get("status")

        with transaction.atomic():
            # Update customer info
            if customer_data:
                customer = instance.customer
                for attr, value in customer_data.items():
                    setattr(customer, attr, value)
                customer.save()

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

            if status == BookingStatus.CANCELLED:
                instance.cancelled_by = self.context["request"].user

            instance.save()

            # Images
            if images:
                SalonMedia.objects.filter(booking=instance).delete()
                SalonMedia.objects.bulk_create(
                    [SalonMedia(booking=instance, image=image) for image in images]
                )

            return instance


class SalonChairBookingSerializer(serializers.ModelSerializer):
    customer = SalonCustomerSlimSerializer()
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
    employee = serializers.SlugRelatedField(
        queryset=Employee.objects.all(),
        slug_field="uid",
        required=False,
        allow_null=True,
    )

    def to_representation(self, instance):
        rep = super().to_representation(instance)

        rep["services"] = BookingServicesSlimSerializer(
            instance.services.all(), many=True
        ).data

        rep["products"] = BookingProductsSlimSerializer(
            instance.products.all(), many=True
        ).data

        rep["employee"] = (
            {"uid": instance.employee.uid, "name": instance.employee.name}
            if instance.employee
            else None
        )

        return rep

    class Meta:
        model = Booking
        fields = [
            "uid",
            "customer",
            "booking_id",
            "booking_date",
            "booking_time",
            "status",
            "booking_duration",
            "notes",
            "services",
            "products",
            "employee",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["booking_duration", "booking_id"]

    def create(self, validated_data):
        customer = validated_data.pop("customer")
        services = validated_data.pop("services", [])
        products = validated_data.pop("products", [])
        employee = validated_data.pop("employee", None)
        account = self.context["request"].account

        with transaction.atomic():
            customer_source = customer.get("source", "Booking")

            source = get_or_create_category(
                customer_source, account, category_type=CategoryType.CUSTOMER_SOURCE
            )

            customer_obj, _ = Customer.objects.get_or_create(
                account=validated_data["account"],
                phone=customer["phone"],
                defaults={
                    "first_name": customer["first_name"],
                    "last_name": customer["last_name"],
                    "email": customer.get("email"),
                    "source": source,
                    "type": CustomerType.CUSTOMER,
                    "salon": validated_data["salon"],
                },
            )
            validated_data["customer"] = customer_obj

            total_duration = sum(
                (service.service_duration for service in services), timedelta()
            )
            validated_data["booking_duration"] = total_duration

            if employee:
                validated_data["employee"] = employee

            booking = Booking.objects.create(**validated_data)
            booking.services.set(services)
            if products:
                booking.products.set(products)

            return booking

    def update(self, instance, validated_data):
        customer_data = validated_data.pop("customer", None)
        services = validated_data.pop("services", None)
        products = validated_data.pop("products", None)
        employee = validated_data.pop("employee", None)

        with transaction.atomic():
            # Update customer info
            if customer_data:
                customer = instance.customer
                for attr, value in customer_data.items():
                    setattr(customer, attr, value)
                customer.save()

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

            # Update employee
            if employee is not None:
                instance.employee = employee

            instance.save()

            return instance


class SalonChairSlimSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chair
        fields = ["uid", "name", "type", "status", "created_at", "updated_at"]


class BookingCalendarSlimSerializer(serializers.ModelSerializer):
    services = ServiceSlimSerializer(many=True)
    customer = CustomerSlimSerializer()

    class Meta:
        model = Booking
        fields = [
            "uid",
            "booking_date",
            "booking_time",
            "completed_at",
            "booking_duration",
            "status",
            "services",
            "customer",
            "created_at",
        ]


class SalonBookingCalendarSerializer(serializers.ModelSerializer):
    bookings = BookingCalendarSlimSerializer(
        many=True, read_only=True, source="employee_bookings"
    )

    class Meta:
        model = Employee
        fields = [
            "uid",
            "image",
            "name",
            "bookings",
        ]


class SalonBookingCalendarDetailSerializer(serializers.ModelSerializer):
    customer = CustomerSlimSerializer(read_only=True)
    employee = serializers.SlugRelatedField(
        slug_field="uid",
        queryset=Employee.objects.all(),
        required=False,
        allow_null=True,
    )
    services = serializers.SlugRelatedField(
        slug_field="uid",
        queryset=Service.objects.all(),
        many=True,
    )
    products = serializers.SlugRelatedField(
        slug_field="uid",
        queryset=Product.objects.all(),
        many=True,
    )
    total_products = serializers.SerializerMethodField()
    total_products_price = serializers.SerializerMethodField()
    total_services = serializers.SerializerMethodField()
    total_services_price = serializers.SerializerMethodField()
    services_discount_price = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    final_price = serializers.SerializerMethodField()
    images = serializers.ListField(
        child=serializers.ImageField(), required=False, write_only=True
    )

    class Meta:
        model = Booking
        fields = [
            "uid",
            "booking_date",
            "booking_time",
            "booking_duration",
            "completed_at",
            "status",
            "cancellation_reason",
            "notes",
            "customer",
            "services",
            "total_services",
            "total_services_price",
            "services_discount_price",
            "products",
            "total_products",
            "total_products_price",
            "employee",
            "created_at",
            "images",
            "tips_amount",
            "payment_type",
            "total_price",
            "final_price",
        ]

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
        final_services_price = sum(s.final_price() for s in obj.services.all())
        total_products_price = sum(p.price for p in obj.products.all())
        return final_services_price + total_products_price + obj.tips_amount

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        images_qs = SalonMedia.objects.filter(booking=instance)

        rep["services"] = ServiceSlimSerializer(instance.services.all(), many=True).data
        rep["products"] = ProductSlimSerializer(instance.products.all(), many=True).data
        rep["employee"] = EmployeeSlimSerializer(
            instance.employee, context=self.context
        ).data
        rep["images"] = MediaSlimSerializer(
            images_qs, many=True, context=self.context
        ).data
        return rep

    def validate(self, attrs):
        images = attrs.get("images", [])
        status = attrs.get("status")
        cancellation_reason = attrs.get("cancellation_reason", None)
        errors = {}

        if len(images) > 3:
            errors["images"] = [_("A maximum of three images can be uploaded.")]

        if status == BookingStatus.CANCELLED and not cancellation_reason:
            errors["cancellation_reason"] = [
                _("Cancellation reason is required when booking is cancelled.")
            ]

        if errors:
            raise serializers.ValidationError(errors)
        return attrs

    @transaction.atomic
    def update(self, instance, validated_data):
        images = validated_data.pop("images", [])
        services = validated_data.pop("services", None)
        products = validated_data.pop("products", None)
        employee = validated_data.pop("employee", None)
        status = validated_data.get("status")

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if status == BookingStatus.CANCELLED:
            instance.cancelled_by = self.context["request"].user

        if services is not None:
            instance.services.set(services)
        if products is not None:
            instance.products.set(products)
        if employee is not None:
            instance.employee = employee

        instance.save()

        if images:
            SalonMedia.objects.filter(booking=instance).delete()
            SalonMedia.objects.bulk_create(
                [SalonMedia(booking=instance, image=image) for image in images]
            )

        return instance


class SalonLookBookSerializer(serializers.ModelSerializer):
    images = serializers.ListField(
        child=serializers.ImageField(), write_only=True, required=False
    )
    customer = CustomerSlimSerializer(read_only=True)

    class Meta:
        model = Booking
        fields = [
            "uid",
            "booking_id",
            "customer",
            "completed_at",
            "images",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "uid",
            "booking_id",
            "customer",
            "completed_at",
            "created_at",
            "updated_at",
        ]

    def validate_images(self, value):
        """
        Ensure at least one image is provided.
        """
        if len(value) == 0:
            raise serializers.ValidationError("At least one image must be provided.")

        if len(value) > 3:
            raise serializers.ValidationError(
                "A maximum of three images can be uploaded."
            )
        return value

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        request = self.context.get("request")
        images_qs = SalonMedia.objects.filter(booking=instance)
        rep["images"] = [
            {
                **BookingImageSlimSerializer(img, context={"request": request}).data,
                "image": (
                    request.build_absolute_uri(img.image.url)
                    if request
                    else img.image.url
                ),
            }
            for img in images_qs
        ]
        return rep

    def update(self, instance, validated_data):
        images = validated_data.pop("images", [])

        with transaction.atomic():
            SalonMedia.objects.filter(booking=instance).delete()

            for image in images:
                SalonMedia.objects.create(booking=instance, image=image)

            return instance


class ServiceCategoryRevenueSerializer(serializers.Serializer):
    category_uid = serializers.UUIDField()
    category_name = serializers.CharField()
    revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2)


class ProductCategoryRevenueSerializer(serializers.Serializer):
    category_uid = serializers.UUIDField()
    category_name = serializers.CharField()
    revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2)


class ServiceRevenueSerializer(serializers.Serializer):
    service_uid = serializers.UUIDField()
    service_name = serializers.CharField()
    category_name = serializers.CharField()
    revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    booking_count = serializers.IntegerField()


class ProductRevenueSerializer(serializers.Serializer):
    product_uid = serializers.UUIDField()
    product_name = serializers.CharField()
    category_name = serializers.CharField()
    revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    booking_count = serializers.IntegerField()

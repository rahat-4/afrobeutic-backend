from datetime import datetime, timedelta, time

from django.db import transaction

from rest_framework import serializers
from rest_framework.generics import get_object_or_404

from apps.authentication.models import AccountMembership, AccountMembershipRole
from apps.salon.models import (
    Salon,
    OpeningHours,
    SalonMedia,
    Service,
    Product,
    Chair,
    Employee,
    Customer,
    Booking,
)

from common.serializers import CustomerSlimSerializer


class OpeningHoursSerializer(serializers.ModelSerializer):

    class Meta:
        model = OpeningHours
        exclude = ["salon", "created_at", "updated_at"]


class SalonSerializer(serializers.ModelSerializer):
    opening_hours = OpeningHoursSerializer(many=True, required=False)

    class Meta:
        model = Salon
        fields = [
            "uid",
            "logo",
            "name",
            "salon_type",
            "email",
            "phone",
            "website",
            "street",
            "city",
            "postal_code",
            "country",
            "latitude",
            "longitude",
            "status",
            "opening_hours",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        opening_hours = attrs.get("opening_hours", [])
        errors = {}

        # Validate each day's opening hours
        opening_hours_errors = {}

        for _, day in enumerate(opening_hours):
            day_errors = {}

            is_closed = day.get("is_closed", False)

            # Default times to 00:00:00 if not provided
            opening_start = day.get("opening_start_time") or time(0, 0)
            opening_end = day.get("opening_end_time") or time(0, 0)
            break_start = day.get("break_start_time") or time(0, 0)
            break_end = day.get("break_end_time") or time(0, 0)

            if (
                any(
                    t == time(0, 0)
                    for t in [opening_start, opening_end, break_start, break_end]
                )
                and not is_closed
            ):
                opening_hours_errors[f"{day['day'].capitalize()}"] = [
                    "All fields must be provided unless the day is marked as closed."
                ]
            elif not is_closed:
                # Validate opening times
                if opening_start >= opening_end:
                    opening_hours_errors[f"{day['day'].capitalize()}"] = [
                        "Opening start time must be before end time."
                    ]

                # Validate break times if not all zero
                if (break_start != time(0, 0)) or (break_end != time(0, 0)):
                    if not (opening_start <= break_start < break_end <= opening_end):
                        opening_hours_errors[f"{day['day'].capitalize()}"] = [
                            "Break time must be within the opening hours range."
                        ]
                    else:
                        break_duration = datetime.combine(
                            datetime.today(), break_end
                        ) - datetime.combine(datetime.today(), break_start)

                        if break_duration > timedelta(hours=2):
                            opening_hours_errors[f"{day['day'].capitalize()}"] = [
                                "Break time cannot exceed 2 hours."
                            ]

            if day_errors:
                opening_hours_errors[f"{day['day'].capitalize()}"] = day_errors

        if opening_hours_errors:
            errors["opening_hours"] = opening_hours_errors

        if errors:
            raise serializers.ValidationError(errors)

        return attrs

    def create(self, validated_data):
        with transaction.atomic():
            opening_hours = validated_data.pop("opening_hours", [])
            salon = Salon.objects.create(**validated_data)

            for opening_hour in opening_hours:
                OpeningHours.objects.create(salon=salon, **opening_hour)
            return salon

    def update(self, instance, validated_data):
        with transaction.atomic():
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


class SalonEmployeeSlimSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ["uid", "employee_id", "name", "phone", "designation", "image"]


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

    class Meta:
        model = Service
        fields = [
            "uid",
            "name",
            "category",
            "price",
            "description",
            "images",
            "uploaded_images",
            "service_duration",
            "available_time_slots",
            "gender_specific",
            "discount_percentage",
            "assign_employees",
            "created_at",
            "updated_at",
        ]

    def validate_uploaded_images(self, value):
        """
        Ensure no more than 2 images are uploaded.
        """
        if len(value) > 2:
            raise serializers.ValidationError("You can upload a maximum of 2 images.")
        return value

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["assign_employees"] = SalonEmployeeSlimSerializer(
            instance.assign_employees.all(), many=True
        ).data

        return rep

    def create(self, validated_data):
        uploaded_images = validated_data.pop("uploaded_images", [])
        assign_employees = validated_data.pop("assign_employees", [])

        with transaction.atomic():
            service = Service.objects.create(**validated_data)

            # Create images
            for index, image in enumerate(uploaded_images):
                SalonMedia.objects.create(service=service, image=image)

            return service

    def update(self, instance, validated_data):
        uploaded_images = validated_data.pop("uploaded_images", None)
        assign_employees = validated_data.pop("assign_employees", [])

        with transaction.atomic():
            # Update service fields
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            if assign_employees != []:
                instance.assign_employees.set(assign_employees)

            # If new images are uploaded, replace old ones
            if uploaded_images is not None:
                # Delete old images
                SalonMedia.objects.filter(service=instance).delete()

                # Create new images
                for index, image in enumerate(uploaded_images):
                    SalonMedia.objects.create(service=instance, image=image)

            return instance


class SalonProductSerializer(serializers.ModelSerializer):
    images = SalonMediaSerializer(many=True, read_only=True, source="product_images")
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(), write_only=True, required=False
    )

    class Meta:
        model = Product
        fields = [
            "uid",
            "name",
            "category",
            "price",
            "description",
            "images",
            "uploaded_images",
            "created_at",
            "updated_at",
        ]

    def validate_uploaded_images(self, value):
        """
        Ensure no more than 2 images are uploaded.
        """
        if len(value) > 2:
            raise serializers.ValidationError("You can upload a maximum of 2 images.")
        return value

    def create(self, validated_data):
        uploaded_images = validated_data.pop("uploaded_images", [])

        with transaction.atomic():
            product = Product.objects.create(**validated_data)

            # Create images
            for index, image in enumerate(uploaded_images):
                SalonMedia.objects.create(product=product, image=image)

            return product

    def update(self, instance, validated_data):
        uploaded_images = validated_data.pop("uploaded_images", None)

        with transaction.atomic():
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
                Employee.objects.filter(account=account, salon=salon, employee_id=value)
                .exclude(uid=self.instance.uid)
                .exists()
            ):
                raise serializers.ValidationError(
                    "Employee ID must be unique within the salon."
                )
        else:
            if Employee.objects.filter(
                account=account, salon=salon, employee_id=value
            ).exists():
                raise serializers.ValidationError(
                    "Employee ID must be unique within the salon."
                )
        return value


class SalonChairSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chair
        fields = ["uid", "name", "type", "status", "created_at", "updated_at"]


class SalonCustomerSlimSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["uid", "name", "phone", "created_at", "updated_at"]


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


class SalonChairBookingSerializer(serializers.ModelSerializer):
    customer = SalonCustomerSlimSerializer()
    services = serializers.SlugRelatedField(
        queryset=Service.objects.all(), many=True, slug_field="uid"
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

        with transaction.atomic():
            customer_obj, _ = Customer.objects.get_or_create(
                account=validated_data["account"],
                phone=customer["phone"],
                defaults={"name": customer["name"], "salon": validated_data["salon"]},
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


class SalonChairSlimSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chair
        fields = ["uid", "name", "type", "status", "created_at", "updated_at"]


class SalonBookingSerializer(serializers.ModelSerializer):
    customer = SalonCustomerSlimSerializer()
    chair = SalonChairSlimSerializer()
    services = BookingServicesSlimSerializer(many=True, read_only=True)
    products = BookingProductsSlimSerializer(many=True, read_only=True)
    employee = serializers.SerializerMethodField()

    def get_employee(self, obj):
        if obj.employee:
            return {"uid": obj.employee.uid, "name": obj.employee.name}
        return None

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
            "chair",
            "services",
            "products",
            "employee",
            "created_at",
            "updated_at",
        ]


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

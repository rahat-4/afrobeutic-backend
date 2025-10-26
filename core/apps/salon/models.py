from datetime import timedelta

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

from django_countries.fields import CountryField
from phonenumber_field.modelfields import PhoneNumberField

from common.models import BaseModel

from apps.authentication.models import Account

from .choices import (
    SalonType,
    SalonStatus,
    DaysOfWeek,
    BookingStatus,
    ChairStatus,
    ServiceTimeSlot,
)
from .utils import (
    get_salon_media_path,
    get_salon_logo_path,
    get_salon_employee_image_path,
    unique_booking_id_generator,
    validate_available_time_slots,
)

User = get_user_model()


class Salon(BaseModel):
    logo = models.ImageField(upload_to=get_salon_logo_path, blank=True, null=True)
    name = models.CharField(max_length=255)
    salon_type = models.CharField(
        max_length=10, choices=SalonType.choices, default=SalonType.MALE
    )
    email = models.EmailField()
    phone = PhoneNumberField()
    website = models.URLField(blank=True, null=True)
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = CountryField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    status = models.CharField(
        max_length=10, choices=SalonStatus.choices, default=SalonStatus.ACTIVE
    )

    # Fk
    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="account_salons"
    )

    def __str__(self):
        return f"{self.name} - {self.city} - Owner: {self.account.name}"


class OpeningHours(BaseModel):
    day = models.CharField(max_length=20, choices=DaysOfWeek.choices)
    opening_start_time = models.TimeField(blank=True, null=True)
    opening_end_time = models.TimeField(blank=True, null=True)
    break_start_time = models.TimeField(blank=True, null=True)
    break_end_time = models.TimeField(blank=True, null=True)
    is_closed = models.BooleanField(default=False)

    # Fk
    salon = models.ForeignKey(
        Salon, on_delete=models.CASCADE, related_name="opening_hours"
    )

    def __str__(self):
        return f"Salon: {self.salon.name} - {self.day}: Closed: {self.is_closed}"


class SalonMedia(BaseModel):
    service = models.ForeignKey(
        "Service",
        on_delete=models.SET_NULL,
        related_name="service_images",
        null=True,
        blank=True,
    )
    product = models.ForeignKey(
        "Product",
        on_delete=models.SET_NULL,
        related_name="product_images",
        null=True,
        blank=True,
    )
    booking = models.ForeignKey(
        "Booking",
        on_delete=models.SET_NULL,
        related_name="booking_images",
        null=True,
        blank=True,
    )
    image = models.ImageField(upload_to=get_salon_media_path)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Media {self.uid}"


class Service(BaseModel):
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=300, blank=True, null=True)
    service_duration = models.DurationField(default=timedelta(minutes=30))
    available_time_slots = models.JSONField(
        default=list,
        validators=[validate_available_time_slots],
        help_text="List of available time slots. Example: ['MORNING', 'AFTERNOON']",
    )
    gender_specific = models.CharField(
        max_length=10, choices=SalonType.choices, default=SalonType.UNISEX
    )
    discount_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00
    )

    # Fk
    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="account_services"
    )
    salon = models.ForeignKey(
        Salon, on_delete=models.CASCADE, related_name="salon_services"
    )
    assign_employees = models.ManyToManyField(
        "Employee", related_name="employee_services", blank=True
    )

    def __str__(self):
        return f"UID: {self.uid} - {self.name} - {self.salon.name}"


class Product(BaseModel):
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=300, blank=True, null=True)

    # Fk
    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="account_products"
    )
    salon = models.ForeignKey(
        Salon, on_delete=models.CASCADE, related_name="salon_products"
    )

    def __str__(self):
        return f"UID: {self.uid} - {self.name} - {self.salon.name}"


class Employee(BaseModel):
    employee_id = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    phone = PhoneNumberField()
    designation = models.CharField(max_length=100)
    image = models.ImageField(
        upload_to=get_salon_employee_image_path, blank=True, null=True
    )

    # Fk
    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="account_employees"
    )
    salon = models.ForeignKey(
        Salon, on_delete=models.CASCADE, related_name="salon_employees"
    )

    class Meta:
        unique_together = ["account", "salon", "employee_id"]

    def __str__(self):
        return f"UID{self.uid} - {self.name} - {self.salon.name}"


class Chair(BaseModel):
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=100)
    status = models.CharField(
        max_length=20, choices=ChairStatus.choices, default=ChairStatus.AVAILABLE
    )

    # Fk
    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="account_chairs"
    )
    salon = models.ForeignKey(
        Salon, on_delete=models.CASCADE, related_name="salon_chairs"
    )

    def __str__(self):
        return f"{self.name} - {self.salon.name}"


class Customer(BaseModel):
    name = models.CharField(max_length=100)
    phone = PhoneNumberField()

    # Fk
    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="account_customers"
    )
    salon = models.ForeignKey(
        Salon, on_delete=models.CASCADE, related_name="salon_customers"
    )

    class Meta:
        unique_together = ["account", "phone"]

    def __str__(self):
        return f"{self.name} - {self.salon.name}"


class Booking(BaseModel):
    booking_id = models.CharField(max_length=8)
    booking_date = models.DateField()
    booking_time = models.TimeField()
    status = models.CharField(
        max_length=15, choices=BookingStatus.choices, default=BookingStatus.PLACED
    )
    notes = models.TextField(blank=True, null=True)
    booking_duration = models.DurationField(default=timedelta(minutes=30))
    cancellation_reason = models.TextField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    # Fk
    cancelled_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="user_cancelled_bookings",
        null=True,
        blank=True,
    )
    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="account_bookings"
    )
    salon = models.ForeignKey(
        Salon, on_delete=models.CASCADE, related_name="salon_bookings"
    )
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="customer_bookings"
    )
    chair = models.ForeignKey(
        Chair, on_delete=models.CASCADE, related_name="chair_bookings"
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        related_name="employee_bookings",
        null=True,
        blank=True,
    )

    # M2M
    services = models.ManyToManyField(Service, related_name="service_bookings")
    products = models.ManyToManyField(
        Product, related_name="product_bookings", blank=True
    )

    class Meta:
        ordering = ["-booking_date", "-booking_time"]
        indexes = [
            models.Index(fields=["booking_date", "booking_time"]),
            models.Index(fields=["salon", "status"]),
        ]

    def save(self, *args, **kwargs):
        if not self.booking_id:
            self.booking_id = unique_booking_id_generator(self)

        if self.status == BookingStatus.COMPLETED and not self.completed_at:
            self.completed_at = timezone.now()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Booking {self.uid} - {self.customer.name} on {self.booking_date} at {self.booking_time}"

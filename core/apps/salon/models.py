from django.db import models
from django.contrib.auth import get_user_model

from django_countries.fields import CountryField
from phonenumber_field.modelfields import PhoneNumberField

from common.models import BaseModel

from apps.authentication.models import Account

from .choices import (
    SalonType,
    SalonStatus,
    ServiceCategory,
    DaysOfWeek,
    BookingStatus,
)
from .utils import get_salon_media_path

User = get_user_model()


class Salon(BaseModel):
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
        max_length=10, choices=SalonStatus.choices, default=SalonStatus.OPEN
    )

    # Fk
    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="account_salons"
    )

    def __str__(self):
        return f"{self.name} - {self.city}"


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
    image = models.ImageField(upload_to=get_salon_media_path)
    order = models.PositiveIntegerField(default=0)
    is_primary = models.BooleanField(default=False)

    class Meta:
        ordering = ["order", "-created_at"]

    def __str__(self):
        name = (
            self.service.name
            if self.service
            else (self.product.name if self.product else "No media")
        )
        return f"Media for {name}"


class Service(BaseModel):
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=300, blank=True, null=True)

    # Fk
    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="account_services"
    )
    salon = models.ForeignKey(
        Salon, on_delete=models.CASCADE, related_name="salon_services"
    )
    image = models.ImageField(upload_to=get_salon_media_path)

    def __str__(self):
        return f"{self.name} - {self.salon.name}"


class Product(BaseModel):
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=50, choices=ServiceCategory.choices)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=300, blank=True, null=True)
    images = models.ManyToManyField(
        SalonMedia, blank=True, related_name="product_images"
    )

    # Fk
    salon = models.ForeignKey(
        Salon, on_delete=models.CASCADE, related_name="salon_products"
    )

    def __str__(self):
        return f"{self.name} - {self.salon.name}"


class Chair(BaseModel):
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=100)

    # Fk
    salon = models.ForeignKey(
        Salon, on_delete=models.CASCADE, related_name="salon_chairs"
    )

    def __str__(self):
        return f"{self.name} - {self.salon.name}"


class Booking(BaseModel):
    booking_date = models.DateField()
    booking_time = models.TimeField()
    status = models.CharField(
        max_length=15, choices=BookingStatus.choices, default=BookingStatus.PLACED
    )
    notes = models.TextField(blank=True, null=True)

    # Fk
    salon = models.ForeignKey(
        Salon, on_delete=models.CASCADE, related_name="salon_bookings"
    )
    service = models.ForeignKey(
        Service, on_delete=models.CASCADE, related_name="service_bookings"
    )
    chair = models.ForeignKey(
        Chair, on_delete=models.CASCADE, related_name="chair_bookings"
    )

    def __str__(self):
        return f"Booking for {self.customer_name} at {self.salon.name} on {self.appointment_date}"

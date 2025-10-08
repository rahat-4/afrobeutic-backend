from django.db import models

from django_countries.fields import CountryField
from phonenumber_field.modelfields import PhoneNumberField

from common.models import BaseModel

from .choices import SalonType


class Salon(BaseModel):
    name = models.CharField(max_length=255)
    salon_type = models.CharField(
        max_length=10, choices=SalonType.choices, default=SalonType.MALE
    )
    email = models.EmailField(unique=True)
    phone = PhoneNumberField(unique=True)
    website = models.URLField(blank=True, null=True)
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = CountryField()
    latitude = models.FloatField()
    longitude = models.FloatField()

    def __str__(self):
        return f"{self.name} - {self.city}"

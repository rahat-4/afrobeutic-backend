from django.db import models


class SalonType(models.TextChoices):
    UNISEX = "UNISEX", "Unisex"
    MALE = "MALE", "Male"
    FEMALE = "FEMALE", "Female"

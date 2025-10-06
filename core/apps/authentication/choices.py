from django.db import models


class UserGender(models.TextChoices):
    MALE = "MALE", "Male"
    FEMALE = "FEMALE", "Female"
    OTHER = "OTHER", "Other"


class UserRole(models.TextChoices):
    MANAGEMENT_OWNER = "MANAGEMENT_OWNER", "Management Owner"
    MANAGEMENT_STAFF = "MANAGEMENT_STAFF", "Management Staff"
    OWNER = "OWNER", "Owner"
    ADMIN = "ADMIN", "Admin"
    STAFF = "STAFF", "Staff"

from django.db import models


class UserGender(models.TextChoices):
    MALE = "MALE", "Male"
    FEMALE = "FEMALE", "Female"
    OTHER = "OTHER", "Other"


class AccountMembershipRole(models.TextChoices):
    MANAGEMENT_ADMIN = "MANAGEMENT_ADMIN", "Management Admin"
    MANAGEMENT_STAFF = "MANAGEMENT_STAFF", "Management Staff"
    OWNER = "OWNER", "Owner"
    ADMIN = "ADMIN", "Admin"
    STAFF = "STAFF", "Staff"

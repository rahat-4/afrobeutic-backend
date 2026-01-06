from django.db import models

class AccountType(models.TextChoices):
    SALON_SHOP = "SALON_SHOP", "Salon Shop"
    INDIVIDUAL_STYLIST = "INDIVIDUAL_STYLIST", "Individual Stylist"

class AccountTimezone(models.TextChoices):
    UTC = "UTC", "UTC (Coordinated Universal Time)"
    EST = "EST", "EST (Eastern Standard Time)"
    CST = "CST", "CST (Central Standard Time)"
    MST = "MST", "MST (Mountain Standard Time)"
    PST = "PST", "PST (Pacific Standard Time)"

class UserGender(models.TextChoices):
    MALE = "MALE", "Male"
    FEMALE = "FEMALE", "Female"
    OTHER = "OTHER", "Other"


class AccountMembershipRole(models.TextChoices):
    OWNER = "OWNER", "Owner"
    ADMIN = "ADMIN", "Admin"
    STAFF = "STAFF", "Staff"


class AccountMembershipStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    INACTIVE = "INACTIVE", "Inactive"
    SUSPENDED = "SUSPENDED", "Suspended"

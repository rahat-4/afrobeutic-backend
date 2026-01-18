from django.db import models


class AccountCategory(models.TextChoices):
    INDIVIDUAL_STYLIST = "INDIVIDUAL_STYLIST", "Individual Stylist"
    SALON_SHOP = "SALON_SHOP", "Salon Shop"


class PlanType(models.TextChoices):
    GOLD = "GOLD", "Gold Plan"
    PLATINUM = "PLATINUM", "Platinum Plan"
    CUSTOM = "CUSTOM", "Custom Plan"


class SubscriptionStatus(models.TextChoices):
    TRIAL = "TRIAL", "Trial"
    ACTIVE = "ACTIVE", "Active"
    EXPIRED = "EXPIRED", "Expired"
    CANCELLED = "CANCELLED", "Cancelled"


class PaymentTransactionStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    COMPLETED = "COMPLETED", "Completed"
    FAILED = "FAILED", "Failed"
    REFUNDED = "REFUNDED", "Refunded"

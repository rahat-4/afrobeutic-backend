from django.db import models
from django.utils.translation import gettext_lazy as _


class SalonType(models.TextChoices):
    UNISEX = "UNISEX", _("Unisex")
    MALE = "MALE", _("Male")
    FEMALE = "FEMALE", _("Female")


class SalonStatus(models.TextChoices):
    ACTIVE = "ACTIVE", _("Active")
    INACTIVE = "INACTIVE", _("Inactive")


class ServiceTimeSlot(models.TextChoices):
    MORNING = "MORNING", _("Morning")
    AFTERNOON = "AFTERNOON", _("Afternoon")
    EVENING = "EVENING", _("Evening")
    AFTER_EVENING = "AFTER_EVENING", _("After Evening")
    ANYTIME = "ANYTIME", _("Anytime")


class DaysOfWeek(models.TextChoices):
    MONDAY = "MONDAY", _("Monday")
    TUESDAY = "TUESDAY", _("Tuesday")
    WEDNESDAY = "WEDNESDAY", _("Wednesday")
    THURSDAY = "THURSDAY", _("Thursday")
    FRIDAY = "FRIDAY", _("Friday")
    SATURDAY = "SATURDAY", _("Saturday")
    SUNDAY = "SUNDAY", _("Sunday")

    def __str__(self):
        return self.label


class BookingStatus(models.TextChoices):
    PLACED = "PLACED", _("Placed")
    INPROGRESS = "INPROGRESS", _("In-progress")
    COMPLETED = "COMPLETED", _("Completed")
    RESCHEDULED = "RESCHEDULED", _("Rescheduled")
    CANCELLED = "CANCELLED", _("Cancelled")
    ABSENT = "ABSENT", _("Absent")


class ChairStatus(models.TextChoices):
    AVAILABLE = "AVAILABLE", _("Available")
    MAINTENANCE = "MAINTENANCE", _("Maintenance")
    OUT_OF_ORDER = "OUT_OF_ORDER", _("Out of Order")


class CustomerType(models.TextChoices):
    LEAD = "LEAD", _("Lead")
    CUSTOMER = "CUSTOMER", _("Customer")

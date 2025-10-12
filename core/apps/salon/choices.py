from django.db import models


class MemberRole(models.TextChoices):
    MANAGEMENT_ADMIN = "MANAGEMENT_ADMIN", "Management Admin"
    MANAGEMENT_STAFF = "MANAGEMENT_STAFF", "Management Staff"
    OWNER = "OWNER", "Owner"
    ADMIN = "ADMIN", "Admin"
    STAFF = "STAFF", "Staff"


class SalonType(models.TextChoices):
    UNISEX = "UNISEX", "Unisex"
    MALE = "MALE", "Male"
    FEMALE = "FEMALE", "Female"


class SalonStatus(models.TextChoices):
    OPEN = "OPEN", "Open"
    CLOSED = "CLOSED", "Closed"


class ServiceCategory(models.TextChoices):
    pass


class DaysOfWeek(models.TextChoices):
    MONDAY = "MONDAY", "Monday"
    TUESDAY = "TUESDAY", "Tuesday"
    WEDNESDAY = "WEDNESDAY", "Wednesday"
    THURSDAY = "THURSDAY", "Thursday"
    FRIDAY = "FRIDAY", "Friday"
    SATURDAY = "SATURDAY", "Saturday"
    SUNDAY = "SUNDAY", "Sunday"

    def __str__(self):
        return self.label


class BookingStatus(models.TextChoices):
    PLACED = "PLACED", "Placed"
    INPROGRESS = "INPROGRESS", "In-progress"
    COMPLETED = "COMPLETED", "Completed"
    RESCHEDULED = "RESCHEDULED", "Rescheduled"
    CANCELLED = "CANCELLED", "Cancelled"
    ABSENT = "ABSENT", "Absent"

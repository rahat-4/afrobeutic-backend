from django.db import models
from django.utils.translation import gettext_lazy as _


class SalonCategory(models.TextChoices):
    GENERAL_SALON = "GENERAL_SALON", _("General Salon")
    MOBILE_OR_HOME_SERVICE_SALON = "MOBILE_OR_HOME_SERVICE_SALON", _(
        "Mobile or Home Service Salon"
    )
    OCCASIONALLY_BOTH = "OCCASIONALLY_BOTH", _("Occasionally Both")


class SalonType(models.TextChoices):
    BARBERSHOP = "BARBERSHOP", _("Barbershop / Men’s Salon")
    UNISEX_SALON = "UNISEX_SALON", _("Unisex Salon")
    LADIES_SALON = "LADIES_SALON", _("Ladies Salon")


class HairServiceType(models.TextChoices):
    AFRO_TEXTURED = "AFRO_TEXTURED", _("Afro-textured (kinky / coily / natural hair)")
    CURLY = "CURLY", _("Curly")
    WAVY = "WAVY", _("Wavy")
    STRAIGHT = "STRAIGHT", _("Straight")
    NOT_SURE = "NOT_SURE", _("Not sure")


class BridalMakeupServiceType(models.TextChoices):
    BRIDAL_MAKEUP = "BRIDAL_MAKEUP", _("Bridal Makeup")
    ENGAGEMENT_PRE_WEDDING_MAKEUP = "ENGAGEMENT_PRE_WEDDING_MAKEUP", _(
        "Engagement / pre-wedding makeup"
    )
    PARTY_EVENING_MAKEUP = "PARTY_EVENING_MAKEUP", _("Party / evening makeup")
    PHOTOSHOOT_EDITORIAL_MAKEUP = "PHOTOSHOOT_EDITORIAL_MAKEUP", _(
        "Photoshoot / editorial makeup"
    )
    TRADITIONAL_CULTURAL_BRIDAL_MAKEUP = "TRADITIONAL_CULTURAL_BRIDAL_MAKEUP", _(
        "Traditional / cultural bridal makeup"
    )
    HD_AIRBRUSH_MAKEUP = "HD_AIRBRUSH_MAKEUP", _("HD / airbrush makeup")
    HAIR_STYLING_FOR_BRIDAL_CLIENTS = "HAIR_STYLING_FOR_BRIDAL_CLIENTS", _(
        "Hair styling for bridal clients"
    )
    GROOM_MAKEUP_GROOMING = "GROOM_MAKEUP_GROOMING", _("Groom makeup / grooming")
    NOT_SURE = "NOT_SURE", _("Not sure")


class AdditionalServiceType(models.TextChoices):
    BEAUTY_SERVICES = "BEAUTY_SERVICES", _("Beauty services")
    NAIL_SERVICES = "NAIL_SERVICES", _("Nail services")
    SPA_SERVICES = "SPA_SERVICES", _("Spa services")
    NONE_OF_THE_ABOVE = "NONE_OF_THE_ABOVE", _("None of the above")


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


class BookingPaymentType(models.TextChoices):
    FRONT_DESK = "FRONT_DESK", _("Front Desk")
    SELF_CHECKOUT = "SELF_CHECKOUT", _("Self Checkout")
    CREDIT_CARD = "CREDIT_CARD", _("Credit Card")
    CASH = "CASH", _("Cash")
    CHECK = "CHECK", _("Check")
    GIFT_CARD = "GIFT_CARD", _("Gift Card")
    VENMO = "VENMO", _("Venmo")
    OTHER = "OTHER", _("Other")

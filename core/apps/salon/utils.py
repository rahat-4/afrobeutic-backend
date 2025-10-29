import random

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from .choices import ServiceTimeSlot


def get_salon_logo_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/salon_<id>/logo/<filename>
    return f"salon_{instance.uid}/logo/{filename}"


def get_salon_employee_image_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/salon_<id>/employees/<filename>
    return f"salon_{instance.salon.uid}/employees/{filename}"


def get_salon_media_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/salon_<id>/<filename>
    return f"salon_{instance.uid}/{filename}"


def unique_booking_id_generator(instance) -> str:
    model = instance.__class__
    unique_number = random.randint(111111, 999999)
    booking_id = f"bk{unique_number}"

    while model.objects.filter(booking_id=booking_id).exists():
        unique_number = random.randint(111111, 999999)
        booking_id = f"bk{unique_number}"

    return booking_id


def validate_available_time_slots(value):
    """
    Custom validator to ensure all values in the JSON list
    are valid ServiceTimeSlot choices.
    """
    valid_choices = [choice[0] for choice in ServiceTimeSlot.choices]
    invalid = [v for v in value if v not in valid_choices]
    if invalid:
        raise ValidationError(
            _(f"Invalid time slot(s): {invalid}. " f"Allowed values: {valid_choices}")
        )

import random


def get_salon_logo_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/salon_<id>/logo/<filename>
    return f"salon_{instance.uid}/logo/{filename}"


def get_salon_employee_image_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/salon_<id>/employees/<filename>
    return f"salon_{instance.salon.uid}/employees/{filename}"


def get_salon_media_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/salon_<id>/<filename>
    return f"salon_{instance.uid}/{filename}"
    return


def unique_booking_id_generator(instance) -> str:
    model = instance.__class__
    unique_number = random.randint(111111, 999999)
    booking_id = f"bk{unique_number}"

    while model.objects.filter(booking_id=booking_id).exists():
        unique_number = random.randint(111111, 999999)
        booking_id = f"bk{unique_number}"

    return booking_id

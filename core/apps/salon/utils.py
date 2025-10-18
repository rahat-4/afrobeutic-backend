def get_salon_logo_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/salon_<id>/logo/<filename>
    return f"salon_{instance.uid}/logo/{filename}"


def get_salon_employee_image_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/salon_<id>/employees/<filename>
    return f"salon_{instance.salon.uid}/employees/{filename}"


def get_salon_media_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/salon_<id>/<filename>
    return f"salon_{instance.service.uid if instance.service else instance.product.uid}/{filename}"
    return

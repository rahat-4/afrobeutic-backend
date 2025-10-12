def get_salon_media_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/salon_<id>/<filename>
    return f"salon_{instance.service.uid if instance.service else instance.product.uid}/{filename}"
    return

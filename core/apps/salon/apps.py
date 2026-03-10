from django.apps import AppConfig


class SalonConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.salon"

    def ready(self):
        from apps.salon.signals import register_booking_signals

        register_booking_signals()

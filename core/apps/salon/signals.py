from django.db.models.signals import post_save
from django.dispatch import receiver


def register_booking_signals():
    """Call this from SalonConfig.ready()"""
    from apps.salon.models import Booking
    from common.email_notifications import (
        send_new_booking_admin_email,
        send_new_booking_customer_email,
    )

    @receiver(post_save, sender=Booking, weak=False)
    def on_booking_created(sender, instance, created, **kwargs):
        if not created:
            return
        try:
            send_new_booking_admin_email(instance)
        except Exception as exc:
            import logging

            logging.getLogger(__name__).warning(
                "Admin booking email failed for booking %s: %s", instance.uid, exc
            )
        try:
            send_new_booking_customer_email(instance)
        except Exception as exc:
            import logging

            logging.getLogger(__name__).warning(
                "Customer booking email failed for booking %s: %s", instance.uid, exc
            )

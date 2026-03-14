# from django.db.models.signals import post_save
# from django.dispatch import receiver


# def register_account_signals():
#     """Call this from AuthenticationConfig.ready()"""
#     from apps.authentication.models import Account
#     from common.email_notifications import (
#         send_new_client_registration_owner_email,
#         send_new_client_welcome_email,
#     )

#     @receiver(post_save, sender=Account, weak=False)
#     def on_account_created(sender, instance, created, **kwargs):
#         if not created:
#             return
#         try:
#             send_new_client_registration_owner_email(instance)
#         except Exception as exc:
#             import logging

#             logging.getLogger(__name__).warning(
#                 "Owner registration email failed for account %s: %s", instance.uid, exc
#             )
#         try:
#             send_new_client_welcome_email(instance)
#         except Exception as exc:
#             import logging

#             logging.getLogger(__name__).warning(
#                 "Welcome email failed for account %s: %s", instance.uid, exc
#             )

from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.authentication"

    # def ready(self):
    #     from apps.authentication.signals import register_account_signals

    #     register_account_signals()

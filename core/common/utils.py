from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils import timezone
from datetime import timedelta, datetime, timezone as dt_timezone


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    def __init__(self, expiry_minutes=60):
        super().__init__()
        self.expiry_minutes = expiry_minutes

    def _base36_to_int(self, s):
        return int(s, 36)

    def check_token(self, user, token):
        if not super().check_token(user, token):
            return False

        try:
            ts_b36 = token.split("-")[0]
            ts = self._base36_to_int(ts_b36)
        except (IndexError, ValueError):
            return False

        # Convert timestamp to datetime
        # Django's PasswordResetTokenGenerator uses days since 2001-01-01
        # So we need to convert it back to a datetime
        epoch = datetime(2001, 1, 1, tzinfo=dt_timezone.utc)
        created_time = epoch + timedelta(seconds=ts)
        now = timezone.now()

        # Enforce custom expiration
        if now - created_time > timedelta(minutes=self.expiry_minutes):
            return False

        return True


email_token_generator = EmailVerificationTokenGenerator(expiry_minutes=60)

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils import timezone
from datetime import timedelta


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    def __init__(self, expiry_minutes=60):
        super().__init__()
        self.expiry_minutes = expiry_minutes

    def _get_timestamp(self):
        # Returns current time in seconds since 2001-01-01
        return super()._num_seconds(self._now())

    def check_token(self, user, token):
        if not super().check_token(user, token):
            return False

        # Enforce custom expiration
        ts_b36 = token.split("-")[1]
        ts = self._base36_to_int(ts_b36)

        # Convert token timestamp to datetime
        token_time = self._make_token_with_timestamp(user, ts)
        created_time = self._date(ts)
        now = timezone.now()

        # Enforce 60-minute expiration
        if now - created_time > timedelta(minutes=self.expiry_minutes):
            return False

        return True


email_token_generator = EmailVerificationTokenGenerator(expiry_minutes=60)

import jwt
import random
from datetime import timedelta
from io import BytesIO
from datetime import timedelta, datetime, timezone as dt_timezone
from decimal import Decimal
from weasyprint import HTML

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.conf import settings
from django.utils import timezone
from django.template.loader import render_to_string

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


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


def get_or_create_category(name, account, category_type):
    from .models import Category

    """Retrieve existing or create new category dynamically."""
    name = name.strip().title()
    category, _ = Category.objects.get_or_create(
        name=name, account=account, category_type=category_type, defaults={}
    )
    return category


def get_media_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/media_<id>/<filename>
    return f"media_{instance.uid}/{filename}"


def generate_receipt_pdf(booking):
    """Generate a PDF receipt for a booking."""

    total_amount = Decimal("0.00")

    for service in booking.services.all():
        final_price = service.final_price()

        if isinstance(final_price, Decimal):
            total_amount += final_price
        else:
            total_amount += Decimal(str(final_price))

    for product in booking.products.all():
        if isinstance(product.price, Decimal):
            total_amount += product.price
        else:
            total_amount += Decimal(str(product.price))

    html_string = render_to_string(
        "booking/receipt.html", {"booking": booking, "total_amount": total_amount}
    )

    pdf_file = BytesIO()
    HTML(string=html_string).write_pdf(pdf_file)
    pdf_file.seek(0)

    return pdf_file


def generate_otp():
    """Generate a random 6-digit OTP code."""
    return f"{random.randint(100000, 999999)}"


def otp_expiry(minutes=5):
    return timezone.now() + timedelta(minutes=minutes)

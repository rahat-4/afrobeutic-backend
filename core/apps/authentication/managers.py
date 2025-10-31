from django.contrib.auth.models import BaseUserManager
from django.db import models

from .choices import AccountMembershipRole


class UserManager(BaseUserManager):
    """
    Custom manager for User model where the email is the unique identifier.
    """

    def create_user(self, email, password=None, **extra_fields):
        """
        Creates and saves a regular user with the given email and password.
        """
        if not email:
            raise ValueError("The email address is required")

        if not password:
            raise ValueError("The password is required")

        email = self.normalize_email(email)
        email = email.lower()

        # Additional default or extra field handling
        extra_fields.setdefault("is_active", True)

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Creates and saves a superuser with the given email and password.
        """
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_staff", True)

        if not extra_fields.get("is_superuser"):
            raise ValueError("Superuser must have is_superuser=True.")
        if not extra_fields.get("is_staff"):
            raise ValueError("Superuser must have is_staff=True.")

        return self.create_user(email, password, **extra_fields)


class AccountMembershipQuerySet(models.QuerySet):
    def ordered_by_role(self):
        return self.order_by(
            models.Case(
                models.When(role=AccountMembershipRole.OWNER, then=models.Value(1)),
                models.When(role=AccountMembershipRole.ADMIN, then=models.Value(2)),
                models.When(role=AccountMembershipRole.STAFF, then=models.Value(3)),
                default=models.Value(4),
                output_field=models.IntegerField(),
            )
        )

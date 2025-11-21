from django_countries.fields import CountryField

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from common.models import BaseModel

from .choices import AccountMembershipRole, UserGender, AccountMembershipStatus
from .managers import UserManager, AccountMembershipQuerySet
from .utils import get_user_media_path_prefix


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    avatar = models.ImageField(
        "Avatar",
        upload_to=get_user_media_path_prefix,
        blank=True,
        null=True,
    )
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255, unique=True)
    gender = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        choices=UserGender.choices,
        default=UserGender.OTHER,
    )
    country = CountryField(blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return f"UID: {self.uid} | Email: {self.email}: is_admin={self.is_admin} is_staff={self.is_staff}"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"


class Account(BaseModel):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="created_accounts"
    )

    def __str__(self):
        return f"UID: {self.uid} account: {self.name} owned by {self.owner.email}"


class AccountMembership(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="memberships")
    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="members"
    )
    role = models.CharField(
        max_length=20,
        choices=AccountMembershipRole.choices,
        default=AccountMembershipRole.OWNER,
    )
    status = models.CharField(
        max_length=20,
        choices=AccountMembershipStatus.choices,
        default=AccountMembershipStatus.ACTIVE,
    )
    is_owner = models.BooleanField(default=False)

    objects = AccountMembershipQuerySet.as_manager()

    class Meta:
        unique_together = ["user", "account"]

    def __str__(self):
        return f"{self.user.email} in {self.account.name} as {self.role}"


class AccountInvitation(BaseModel):
    email = models.EmailField(max_length=255)
    invited_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="invitations_sender",
    )
    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="invitations"
    )
    role = models.CharField(
        max_length=20,
        choices=AccountMembershipRole.choices,
        default=AccountMembershipRole.STAFF,
    )
    is_accepted = models.BooleanField(default=False)
    invited_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"Invitation to {self.email} as {self.role} by {self.invited_by.email} | UID: {self.uid}"


# from django.db import models
# from django.utils import timezone
# import uuid


# # ---------------------------------------------------------
# # BILLING PLAN
# # ---------------------------------------------------------


# class Plan(models.Model):
#     code = models.CharField(max_length=50, unique=True)
#     name = models.CharField(max_length=120)
#     price_cents = models.PositiveIntegerField()
#     features = models.JSONField()  # Stores all feature limits
#     is_active = models.BooleanField(default=True)

#     class Meta:
#         db_table = "billing_plan"
#         ordering = ["price_cents"]

#     def __str__(self):
#         return f"{self.name} ({self.code})"


# # ---------------------------------------------------------
# # ACCOUNT SUBSCRIPTION
# # ---------------------------------------------------------


# class Subscription(models.Model):

#     STATUS_CHOICES = [
#         ("trialing", "Trialing"),
#         ("active", "Active"),
#         ("past_due", "Past Due"),
#         ("canceled", "Canceled"),
#         ("paused", "Paused"),
#     ]

#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

#     # Assuming you have an Account model somewhere
#     account = models.ForeignKey(
#         "accounts.Account", on_delete=models.CASCADE, related_name="subscriptions"
#     )

#     plan = models.ForeignKey(
#         Plan, on_delete=models.PROTECT, related_name="subscriptions"
#     )

#     status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")

#     current_period_start = models.DateTimeField(default=timezone.now)
#     current_period_end = models.DateTimeField()

#     cancel_at_period_end = models.BooleanField(default=False)

#     trial_ends_at = models.DateTimeField(null=True, blank=True)

#     # Optional billing provider integration (Stripe, etc.)
#     provider = models.CharField(max_length=20, blank=True, default="")
#     provider_customer_id = models.CharField(max_length=80, blank=True, default="")
#     provider_subscription_id = models.CharField(max_length=80, blank=True, default="")

#     created_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         db_table = "account_subscription"
#         ordering = ["-created_at"]

#     def __str__(self):
#         return f"{self.account} - {self.plan.code} ({self.status})"

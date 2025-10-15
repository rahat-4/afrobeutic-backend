from django_countries.fields import CountryField

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from common.models import BaseModel

from .choices import AccountMembershipRole, UserGender, AccountMembershipStatus
from .managers import UserManager
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
    country = CountryField()

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return f"UID: {self.uid} | Email: {self.email}"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"


class Account(BaseModel):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="created_accounts"
    )

    def __str__(self):
        return f"Account: {self.name} owned by {self.owner.email}"


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

import uuid
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from common.models import BaseModel

from .choices import UserGender, UserRole
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
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.OWNER,
    )
    country = models.CharField(max_length=100, null=True, blank=True)
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


class AccountInvitation(BaseModel):
    email = models.EmailField(max_length=255)
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.STAFF,
    )
    invited_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="invitations_sender",
    )
    is_accepted = models.BooleanField(default=False)
    expires_at = models.DateTimeField()

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"Invitation to {self.email} as {self.role} by {self.invited_by.email}"

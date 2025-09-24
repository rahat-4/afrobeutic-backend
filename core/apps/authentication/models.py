from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from django.contrib.postgres.fields import ArrayField

from common.models import BaseModel

from .choices import UserGender, UserType
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
    user_type = models.CharField(
        max_length=20,
        choices=UserType.choices,
        default=UserType.OWNER,
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

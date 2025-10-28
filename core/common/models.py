from uuid import uuid4

from django.db import models

from .choices import CategoryType


class BaseModel(models.Model):
    uid = models.UUIDField(db_index=True, unique=True, default=uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]


class Category(BaseModel):
    from apps.authentication.models import Account

    name = models.CharField(max_length=100)
    category_type = models.CharField(
        max_length=10, choices=CategoryType.choices, default=CategoryType.SERVICE
    )
    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="account_categories"
    )

    class Meta:
        unique_together = ["account", "name", "category_type"]
        verbose_name_plural = "Categories"

    def __str__(self):
        return f"{self.name} - {self.category_type} - {self.account.name}"

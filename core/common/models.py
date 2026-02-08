from uuid import uuid4

from django.db import models

from .choices import CategoryType
from .utils import get_media_path


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
        max_length=20, choices=CategoryType.choices, default=CategoryType.SERVICE
    )
    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="account_categories"
    )

    class Meta:
        unique_together = ["account", "name", "category_type"]
        verbose_name_plural = "Categories"

    def __str__(self):
        return f"{self.name} - {self.category_type} - {self.account.name}"


class SubCategory(BaseModel):
    from apps.authentication.models import Account

    name = models.CharField(max_length=100)
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="subcategories"
    )
    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="account_subcategories"
    )

    class Meta:
        unique_together = ["account", "name", "category"]
        verbose_name_plural = "SubCategories"

    def __str__(self):
        return f"{self.name} - {self.category.name} - {self.account.name}"


class Media(BaseModel):
    from apps.salon.models import Service, Product, Booking
    from apps.support.models import SupportTicket

    # service = models.ForeignKey(
    #     Service,
    #     on_delete=models.SET_NULL,
    #     related_name="service_images",
    #     null=True,
    #     blank=True,
    # )
    # product = models.ForeignKey(
    #     Product,
    #     on_delete=models.SET_NULL,
    #     related_name="product_images",
    #     null=True,
    #     blank=True,
    # )
    # booking = models.ForeignKey(
    #     Booking,
    #     on_delete=models.SET_NULL,
    #     related_name="booking_images",
    #     null=True,
    #     blank=True,
    # )
    support_ticket = models.ForeignKey(
        SupportTicket,
        on_delete=models.SET_NULL,
        related_name="support_ticket_images",
        null=True,
        blank=True,
    )
    image = models.ImageField(upload_to=get_media_path)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Media: {self.uid}"


class CustomerOtp(BaseModel):
    from apps.salon.models import Customer

    otp_code = models.CharField(max_length=6)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    # Fk
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="otps"
    )

    class Meta:
        indexes = [
            models.Index(fields=["customer", "otp_code"]),
        ]

    def __str__(self):
        return f"OTP for {self.customer.email} | UID: {self.uid}"

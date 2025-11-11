from django.db import models


class CategoryType(models.TextChoices):
    SERVICE = "SERVICE", "Service"
    PRODUCT = "PRODUCT", "Product"
    EMPLOYEE = "EMPLOYEE", "Employee"
    CHAIR = "CHAIR", "Chair"
    LEAD_SOURCE = "LEAD_SOURCE", "Lead Source"

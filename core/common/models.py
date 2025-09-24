from django.db import models

from uuid import uuid4


class BaseModel(models.Model):
    uid = models.UUIDField(db_index=True, unique=True, default=uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]

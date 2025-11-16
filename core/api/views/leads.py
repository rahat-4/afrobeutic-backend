from django_filters.rest_framework import DjangoFilterBackend

from django.shortcuts import get_object_or_404

from rest_framework.generics import ListCreateAPIView, RetrieveUpdateAPIView
from rest_framework import filters

from common.filters import SalonLeadFilter
from common.permissions import (
    IsOwnerOrAdmin,
    IsOwnerOrAdminOrStaff,
)

from apps.salon.choices import CustomerType
from apps.salon.models import Customer

from ..serializers.leads import AccountLeadSerializer


class AccountLeadListView(ListCreateAPIView):
    serializer_class = AccountLeadSerializer
    permission_classes = [IsOwnerOrAdminOrStaff]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = SalonLeadFilter
    search_fields = [
        "first_name",
        "last_name",
        "phone",
        "email",
        "source__name",
    ]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user
        account = self.request.account

        return Customer.objects.filter(
            account=account,
            account__members__user=user,
            type=CustomerType.LEAD,
        )

    def perform_create(self, serializer):
        account = self.request.account

        serializer.save(account=account)


class AccountLeadDetailView(RetrieveUpdateAPIView):
    serializer_class = AccountLeadSerializer
    lookup_url_kwarg = "lead_uid"

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH"]:
            self.permission_classes = [IsOwnerOrAdmin]
        else:
            self.permission_classes = [IsOwnerOrAdminOrStaff]

        return super().get_permissions()

    def get_object(self):
        lead_uid = self.kwargs.get("lead_uid")

        return get_object_or_404(
            Customer,
            uid=lead_uid,
        )

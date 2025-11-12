from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import filters
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveDestroyAPIView,
    RetrieveUpdateDestroyAPIView,
)

from common.permissions import IsOwnerOrAdminOrStaff, IsOwnerOrAdmin

from apps.support.models import SupportTicket, AccountSupportTicket

from ..serializers.supports import (
    SupportTicketSerializer,
    AccountSupportTicketSerializer,
)


class SupportTicketListView(ListCreateAPIView):
    serializer_class = SupportTicketSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            self.permission_classes = [IsOwnerOrAdmin]
        else:
            self.permission_classes = [IsOwnerOrAdminOrStaff]

        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        account = self.request.account

        return SupportTicket.objects.filter(
            account=account, account__members__user=user
        )

    def perform_create(self, serializer):
        account = self.request.account
        serializer.save(account=account)


class SupportTicketDetailView(RetrieveDestroyAPIView):
    serializer_class = SupportTicketSerializer
    permission_classes = [IsOwnerOrAdminOrStaff]

    def get_permissions(self):
        if self.request.method in ["DELETE"]:
            self.permission_classes = [IsOwnerOrAdmin]
        else:
            self.permission_classes = [IsOwnerOrAdminOrStaff]

        return super().get_permissions()

    def get_object(self):
        user = self.request.user
        account = self.request.account
        uid = self.kwargs.get("support_ticket_uid")

        return SupportTicket.objects.get(
            uid=uid, account=account, account__members__user=user
        )


class AccountSupportTicketListView(ListCreateAPIView):
    serializer_class = AccountSupportTicketSerializer
    permission_classes = [IsOwnerOrAdminOrStaff]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["status", "type", "lead__source__name"]
    search_fields = [
        "customer__name",
        "customer__phone",
        "lead__first_name",
        "lead__last_name",
        "lead__email",
        "lead__phone",
        "lead__whatsapp",
    ]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user
        account = self.request.account

        return AccountSupportTicket.objects.filter(
            account=account,
            account__members__user=user,
        )

    def perform_create(self, serializer):
        account = self.request.account
        serializer.save(account=account)


class AccountSupportTicketDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = AccountSupportTicketSerializer

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            self.permission_classes = [IsOwnerOrAdmin]
        else:
            self.permission_classes = [IsOwnerOrAdminOrStaff]

        return super().get_permissions()

    def get_object(self):
        user = self.request.user
        account = self.request.account
        uid = self.kwargs.get("account_support_ticket_uid")

        return AccountSupportTicket.objects.get(
            uid=uid, account=account, account__members__user=user
        )

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import filters
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveDestroyAPIView,
    RetrieveUpdateDestroyAPIView,
)

from common.filters import CustomerEnquiryFilter
from common.permissions import IsOwnerOrAdminOrStaff, IsOwnerOrAdmin

from apps.support.models import SupportTicket, AccountSupportTicket

from ..serializers.supports import (
    AccountEnquirySerializer,
    CustomerEnquirySerializer,
)


class AccountEnquiryListView(ListCreateAPIView):
    serializer_class = AccountEnquirySerializer

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


class AccountEnquiryDetailView(RetrieveDestroyAPIView):
    serializer_class = AccountEnquirySerializer
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
        uid = self.kwargs.get("account_enquiry_uid")

        return SupportTicket.objects.get(
            uid=uid, account=account, account__members__user=user
        )


class CustomerEnquiryListView(ListCreateAPIView):
    serializer_class = CustomerEnquirySerializer
    permission_classes = [IsOwnerOrAdminOrStaff]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = CustomerEnquiryFilter
    search_fields = [
        "customer__first_name",
        "customer__last_name",
        "customer__email",
        "customer__phone",
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


class CustomerEnquiryDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = CustomerEnquirySerializer

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            self.permission_classes = [IsOwnerOrAdmin]
        else:
            self.permission_classes = [IsOwnerOrAdminOrStaff]

        return super().get_permissions()

    def get_object(self):
        user = self.request.user
        account = self.request.account
        uid = self.kwargs.get("customer_enquiry_uid")

        return AccountSupportTicket.objects.get(
            uid=uid, account=account, account__members__user=user
        )

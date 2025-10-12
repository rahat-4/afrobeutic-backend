from rest_framework.generics import (
    CreateAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    get_object_or_404,
)
from rest_framework.response import Response
from rest_framework import status

from apps.authentication.models import AccountMembership, Account

from apps.salon.models import Salon, Service, SalonMedia
from apps.salon.models import SalonStatus

from common.permissions import (
    IsOwner,
    IsOwnerOrAdmin,
    IsOwnerOrAdminOrStaff,
)

from ..serializers.salons import (
    SalonSerializer,
    SalonServiceSerializer,
    SalonMediaSerializer,
)


class SalonListView(ListCreateAPIView):
    serializer_class = SalonSerializer

    def get_permissions(self):

        if self.request.method == "POST":
            self.permission_classes = [IsOwnerOrAdmin]
        else:
            self.permission_classes = [IsOwnerOrAdminOrStaff]

        return super().get_permissions()

    def perform_create(self, serializer):
        account_uid = self.kwargs.get("account_uid")
        account_membership = get_object_or_404(
            AccountMembership,
            account__uid=account_uid,
            user=self.request.user,
        )
        serializer.save(account=account_membership.account)

    def get_queryset(self):
        user = self.request.user
        account_uid = self.kwargs.get("account_uid")

        return Salon.objects.filter(
            account__uid=account_uid, account__members__user=user
        )


class SalonDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = SalonSerializer

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH"]:
            self.permission_classes = [IsOwnerOrAdmin]
        else:
            self.permission_classes = [IsOwnerOrAdminOrStaff]

        return super().get_permissions()

    def get_object(self):
        user = self.request.user
        account_uid = self.kwargs.get("account_uid")
        uid = self.kwargs.get("salon_uid")

        return get_object_or_404(
            Salon, uid=uid, account__uid=account_uid, account__members__user=user
        )


class SalonServiceListView(ListCreateAPIView):
    serializer_class = SalonServiceSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            self.permission_classes = [IsOwnerOrAdmin]
        else:
            self.permission_classes = [IsOwnerOrAdminOrStaff]

        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        account_uid = self.kwargs.get("account_uid")
        salon_uid = self.kwargs.get("salon_uid")

        return Service.objects.filter(
            account__uid=account_uid,
            salon__uid=salon_uid,
            account__members__user=user,
        )

    def perform_create(self, serializer):
        account_uid = self.kwargs.get("account_uid")
        salon_uid = self.kwargs.get("salon_uid")
        account = get_object_or_404(Account, uid=account_uid)
        salon = get_object_or_404(Salon, uid=salon_uid)
        serializer.save(salon=salon, account=account)


class SalonServiceDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = SalonServiceSerializer
    lookup_field = "uid"
    lookup_url_kwarg = "service_uid"

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            self.permission_classes = [IsOwnerOrAdmin]
        else:
            self.permission_classes = [IsOwnerOrAdminOrStaff]

        return super().get_permissions()

    def get_object(self):
        user = self.request.user
        account_uid = self.kwargs.get("account_uid")
        salon_uid = self.kwargs.get("salon_uid")
        service_uid = self.kwargs.get("service_uid")

        return get_object_or_404(
            Service,
            uid=service_uid,
            salon__uid=salon_uid,
            account__uid=account_uid,
            account__members__user=user,
        )

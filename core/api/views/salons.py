from rest_framework.generics import (
    CreateAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    get_object_or_404,
)
from rest_framework.response import Response
from rest_framework import status
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend

from apps.authentication.models import AccountMembership, Account

from apps.salon.models import Salon, Service, SalonMedia, Product
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
    SalonProductSerializer,
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
        account_membership = get_object_or_404(
            AccountMembership,
            account=self.request.account,
            user=self.request.user,
        )
        serializer.save(account=account_membership.account)

    def get_queryset(self):
        user = self.request.user
        account = self.request.account

        return Salon.objects.filter(account=account, account__members__user=user)


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
        account = self.request.account
        uid = self.kwargs.get("salon_uid")

        return get_object_or_404(
            Salon, uid=uid, account=account, account__members__user=user
        )


class SalonServiceListView(ListCreateAPIView):
    serializer_class = SalonServiceSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ["name", "category"]
    ordering_fields = ["created_at", "price"]
    ordering = ["-created_at"]

    def get_permissions(self):
        if self.request.method == "POST":
            self.permission_classes = [IsOwnerOrAdmin]
        else:
            self.permission_classes = [IsOwnerOrAdminOrStaff]

        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        account = self.request.account
        salon_uid = self.kwargs.get("salon_uid")

        return Service.objects.filter(
            account=account,
            salon__uid=salon_uid,
            account__members__user=user,
        )

    def perform_create(self, serializer):
        account = self.request.account
        salon_uid = self.kwargs.get("salon_uid")
        salon = get_object_or_404(Salon, uid=salon_uid, account=account)
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
        account = self.request.account
        salon_uid = self.kwargs.get("salon_uid")
        service_uid = self.kwargs.get("service_uid")

        return get_object_or_404(
            Service,
            uid=service_uid,
            salon__uid=salon_uid,
            account=account,
            account__members__user=user,
        )


class SalonProductListView(ListCreateAPIView):
    serializer_class = SalonProductSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ["name", "category"]
    ordering_fields = ["created_at", "price"]
    ordering = ["-created_at"]

    def get_permissions(self):
        if self.request.method == "POST":
            self.permission_classes = [IsOwnerOrAdmin]
        else:
            self.permission_classes = [IsOwnerOrAdminOrStaff]

        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        account = self.request.account
        salon_uid = self.kwargs.get("salon_uid")

        return Product.objects.filter(
            account=account,
            salon__uid=salon_uid,
            account__members__user=user,
        )

    def perform_create(self, serializer):
        account = self.request.account
        salon_uid = self.kwargs.get("salon_uid")
        salon = get_object_or_404(Salon, uid=salon_uid, account=account)
        serializer.save(salon=salon, account=account)


class SalonProductDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = SalonProductSerializer
    lookup_field = "uid"
    lookup_url_kwarg = "product_uid"

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            self.permission_classes = [IsOwnerOrAdmin]
        else:
            self.permission_classes = [IsOwnerOrAdminOrStaff]

        return super().get_permissions()

    def get_object(self):
        user = self.request.user
        account = self.request.account
        salon_uid = self.kwargs.get("salon_uid")
        product_uid = self.kwargs.get("product_uid")

        return get_object_or_404(
            Product,
            uid=product_uid,
            salon__uid=salon_uid,
            account=account,
            account__members__user=user,
        )


class SalonEmployeeListView(ListCreateAPIView):
    pass

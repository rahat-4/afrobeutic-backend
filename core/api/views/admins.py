from django.contrib.auth import get_user_model
from django.db.models import Prefetch

from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView, RetrieveAPIView

from common.permissions import IsManagementAdminOrStaff

from apps.authentication.models import Account, AccountMembership
from apps.salon.models import Salon, Service, Product, Employee, Booking

from ..serializers.admins import (
    AdminUserSerializer,
    AdminAccountSerializer,
    AdminSalonSerializer,
    AdminServiceSerializer,
    AdminEmployeeSerializer,
    AdminProductSerializer,
    AdminBookingSerializer,
    AdminLookBookSerializer,
)

User = get_user_model()


class AdminUserListView(ListAPIView):
    serializer_class = AdminUserSerializer
    permission_classes = [IsManagementAdminOrStaff]

    def get_queryset(self):
        # Create ordered memberships prefetch
        ordered_memberships = AccountMembership.objects.select_related(
            "account", "account__owner"
        ).ordered_by_role()

        return (
            User.objects.filter(is_staff=False)
            .order_by("created_at")
            .prefetch_related(Prefetch("memberships", queryset=ordered_memberships))
        )


class AdminAccountListView(ListAPIView):
    queryset = Account.objects.all().order_by("created_at")
    serializer_class = AdminAccountSerializer
    permission_classes = [IsManagementAdminOrStaff]


class AdminSalonListView(ListAPIView):
    serializer_class = AdminSalonSerializer
    permission_classes = [IsManagementAdminOrStaff]

    def get_queryset(self):
        account = self.request.account

        return Salon.objects.filter(account=account).order_by("created_at")


class AdminSalonDetailView(RetrieveAPIView):
    queryset = Salon.objects.all()
    serializer_class = AdminSalonSerializer
    permission_classes = [IsManagementAdminOrStaff]

    def get_object(self):
        account = self.request.account
        salon_uid = self.kwargs.get("salon_uid")

        try:
            salon = Salon.objects.get(uid=salon_uid, account=account)
            return salon
        except Salon.DoesNotExist:
            raise ValidationError("Salon not found.")


class AdminServiceListView(ListAPIView):
    serializer_class = AdminServiceSerializer
    permission_classes = [IsManagementAdminOrStaff]

    def get_queryset(self):
        account = self.request.account

        salon_uid = self.kwargs.get("salon_uid")

        try:
            salon = Salon.objects.get(uid=salon_uid, account=account)
            return Service.objects.filter(account=account, salon=salon).order_by(
                "created_at"
            )
        except Salon.DoesNotExist:
            raise ValidationError("Salon not found.")


class AdminProductListView(ListAPIView):
    serializer_class = AdminProductSerializer
    permission_classes = [IsManagementAdminOrStaff]

    def get_queryset(self):
        account = self.request.account

        salon_uid = self.kwargs.get("salon_uid")

        try:
            salon = Salon.objects.get(uid=salon_uid, account=account)
            return Product.objects.filter(account=account, salon=salon).order_by(
                "created_at"
            )
        except Salon.DoesNotExist:
            raise ValidationError("Salon not found.")


class AdminEmployeeListView(ListAPIView):
    serializer_class = AdminEmployeeSerializer
    permission_classes = [IsManagementAdminOrStaff]

    def get_queryset(self):
        account = self.request.account

        salon_uid = self.kwargs.get("salon_uid")

        try:
            salon = Salon.objects.get(uid=salon_uid, account=account)
            return Employee.objects.filter(account=account, salon=salon).order_by(
                "created_at"
            )
        except Salon.DoesNotExist:
            raise ValidationError("Salon not found.")


class AdminBookingListView(ListAPIView):
    serializer_class = AdminBookingSerializer
    permission_classes = [IsManagementAdminOrStaff]

    def get_queryset(self):
        account = self.request.account

        salon_uid = self.kwargs.get("salon_uid")

        try:
            salon = Salon.objects.get(uid=salon_uid, account=account)
            return Booking.objects.filter(account=account, salon=salon).order_by(
                "created_at"
            )
        except Salon.DoesNotExist:
            raise ValidationError("Salon not found.")


class AdminLookBookListView(ListAPIView):
    serializer_class = AdminLookBookSerializer
    permission_classes = [IsManagementAdminOrStaff]

    def get_queryset(self):
        account = self.request.account

        salon_uid = self.kwargs.get("salon_uid")

        try:
            salon = Salon.objects.get(uid=salon_uid, account=account)
            return Booking.objects.filter(account=account, salon=salon).order_by(
                "created_at"
            )
        except Salon.DoesNotExist:
            raise ValidationError("Salon not found.")

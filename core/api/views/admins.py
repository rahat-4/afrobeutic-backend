from django_filters.rest_framework import DjangoFilterBackend

from django.contrib.auth import get_user_model
from django.db.models import Prefetch

from rest_framework import filters
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView, RetrieveAPIView

from common.filters import AdminManagementRoleFilter
from common.permissions import IsManagementAdmin, IsManagementAdminOrStaff

from apps.authentication.choices import AccountMembershipRole
from apps.authentication.emails import send_verification_email
from apps.authentication.models import Account, AccountMembership
from apps.salon.models import Salon, Service, Product, Employee, Booking

from ..serializers.admins import (
    AdminRegistrationSerializer,
    AdminUserSerializer,
    AdminAccountSerializer,
    AdminSalonSerializer,
    AdminServiceSerializer,
    AdminEmployeeSerializer,
    AdminProductSerializer,
    AdminBookingSerializer,
    AdminManagementSerializer,
)

User = get_user_model()


class AdminRegistrationView(APIView):
    serializer_class = AdminRegistrationSerializer
    permission_classes = [IsManagementAdmin]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Send verification email
        send_verification_email(user)

        return Response(
            {"message": "Verification email sent.", "expires_in_minutes": 60},
            status=status.HTTP_201_CREATED,
        )


class AdminManagementListView(ListAPIView):
    serializer_class = AdminManagementSerializer
    permission_classes = [IsManagementAdminOrStaff]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = AdminManagementRoleFilter
    search_fields = ["email", "first_name", "last_name"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        # Return users who are admins or staff
        return User.objects.filter(is_staff=True)


class AdminUserListView(ListAPIView):
    serializer_class = AdminUserSerializer
    permission_classes = [IsManagementAdminOrStaff]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["country"]
    search_fields = ["email", "first_name", "last_name"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        role = self.request.query_params.get("role", None)
        allowed_roles = {
            AccountMembershipRole.OWNER,
            AccountMembershipRole.ADMIN,
            AccountMembershipRole.STAFF,
        }

        memberships_qs = AccountMembership.objects.select_related(
            "account", "account__owner"
        )
        if role in allowed_roles:
            memberships_qs = memberships_qs.filter(role=role).ordered_by_role()
            users_qs = User.objects.filter(is_staff=False, memberships__role=role)
        else:
            memberships_qs = memberships_qs.ordered_by_role()
            users_qs = User.objects.filter(is_staff=False)

        return users_qs.order_by("created_at").prefetch_related(
            Prefetch("memberships", queryset=memberships_qs)
        )


class AdminAccountListView(ListAPIView):
    queryset = Account.objects.all()
    serializer_class = AdminAccountSerializer
    permission_classes = [IsManagementAdminOrStaff]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ["name"]
    ordering_fields = ["created_at", "name"]
    ordering = ["-created_at"]


class AdminSalonListView(ListAPIView):
    serializer_class = AdminSalonSerializer
    permission_classes = [IsManagementAdminOrStaff]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ["name"]
    ordering_fields = ["created_at", "name"]
    ordering = ["-created_at"]
    filterset_fields = ["status", "salon_type"]

    def get_queryset(self):
        account = self.request.account

        return Salon.objects.filter(account=account)


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
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ["name", "assign_employees__name", "assign_employees__employee_id"]
    ordering_fields = [
        "created_at",
        "name",
        "price",
        "discount_percentage",
        "service_duration",
    ]
    ordering = ["-created_at"]
    filterset_fields = ["gender_specific", "category__name"]

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
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ["name"]
    ordering_fields = ["created_at", "name"]
    ordering = ["-created_at"]
    filterset_fields = ["category__name"]

    def get_queryset(self):
        account = self.request.account

        salon_uid = self.kwargs.get("salon_uid")

        try:
            salon = Salon.objects.get(uid=salon_uid, account=account)
            return Product.objects.filter(account=account, salon=salon)
        except Salon.DoesNotExist:
            raise ValidationError("Salon not found.")


class AdminEmployeeListView(ListAPIView):
    serializer_class = AdminEmployeeSerializer
    permission_classes = [IsManagementAdminOrStaff]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ["employee_id", "name"]
    ordering_fields = ["created_at", "name"]
    ordering = ["-created_at"]
    filterset_fields = ["designation__name"]

    def get_queryset(self):
        account = self.request.account

        salon_uid = self.kwargs.get("salon_uid")

        try:
            salon = Salon.objects.get(uid=salon_uid, account=account)
            return Employee.objects.filter(account=account, salon=salon)
        except Salon.DoesNotExist:
            raise ValidationError("Salon not found.")


class AdminBookingListView(ListAPIView):
    serializer_class = AdminBookingSerializer
    permission_classes = [IsManagementAdminOrStaff]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = [
        "booking_id",
        "customer__name",
        "chair__name",
        "employee__name",
        "employee__employee_id",
        "services__name",
        "products__name",
    ]
    ordering_fields = ["created_at", "booking_duration"]
    ordering = ["-created_at"]
    filterset_fields = {
        "booking_date": ["gte", "lte"],
        "status": ["exact"],
    }

    def get_queryset(self):
        account = self.request.account

        salon_uid = self.kwargs.get("salon_uid")

        try:
            salon = Salon.objects.get(uid=salon_uid, account=account)
            return Booking.objects.filter(account=account, salon=salon)
        except Salon.DoesNotExist:
            raise ValidationError("Salon not found.")

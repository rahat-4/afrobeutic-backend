from django_filters.rest_framework import DjangoFilterBackend

from django.contrib.auth import get_user_model
from django.db.models import Prefetch

from rest_framework import filters
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from rest_framework.generics import (
    ListAPIView,
    ListCreateAPIView,
    RetrieveAPIView,
    RetrieveDestroyAPIView,
    RetrieveUpdateDestroyAPIView,
)

from common.filters import AdminManagementRoleFilter
from common.permissions import IsManagementAdmin, IsManagementAdminOrStaff

from apps.authentication.choices import AccountMembershipRole
from apps.authentication.emails import send_verification_email
from apps.authentication.models import Account, AccountMembership
from apps.salon.models import Salon, Service, Product, Employee, Booking
from apps.support.models import SupportTicket

from ..serializers.admin import (
    AdminRegistrationSerializer,
    AdminUserSerializer,
    AdminAccountSerializer,
    AdminSalonSerializer,
    AdminServiceSerializer,
    AdminEmployeeSerializer,
    AdminProductSerializer,
    AdminBookingSerializer,
    AdminManagementSerializer,
    AdminAccountEnquirySerializer,
    AdminSubscriptionPlanSerializer,
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


class AdminManagementDetailView(RetrieveDestroyAPIView):
    serializer_class = AdminManagementSerializer

    def get_permissions(self):
        if self.request.method == "DELETE":
            self.permission_classes = [IsManagementAdmin]
        else:
            self.permission_classes = [IsManagementAdminOrStaff]

        return super().get_permissions()

    def get_object(self):
        uid = self.kwargs.get("management_uid")

        try:
            user = User.objects.get(uid=uid, is_staff=True)
            return user
        except User.DoesNotExist:
            raise ValidationError("Management user not found.")


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


class AdminUserDetailView(RetrieveAPIView):
    serializer_class = AdminUserSerializer
    permission_classes = [IsManagementAdminOrStaff]

    def get_object(self):
        uid = self.kwargs.get("user_uid")

        memberships_qs = AccountMembership.objects.select_related(
            "account", "account__owner"
        )

        try:
            user = (
                User.objects.filter(uid=uid, is_staff=False)
                .prefetch_related(Prefetch("memberships", queryset=memberships_qs))
                .get()
            )
            return user

        except User.DoesNotExist:
            raise ValidationError("User not found.")


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


class AdminAccountDetailView(RetrieveAPIView):
    queryset = Account.objects.all()
    serializer_class = AdminAccountSerializer
    permission_classes = [IsManagementAdminOrStaff]
    lookup_field = "uid"
    lookup_url_kwarg = "account_uid"


class AdminSalonListView(ListAPIView):
    serializer_class = AdminSalonSerializer
    permission_classes = [IsManagementAdminOrStaff]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["status", "salon_type"]
    search_fields = ["name"]
    ordering_fields = ["created_at", "name"]
    ordering = ["-created_at"]

    def get_queryset(self):
        account_uid = self.kwargs.get("account_uid")

        return Salon.objects.filter(account__uid=account_uid)


class AdminSalonDetailView(RetrieveAPIView):
    queryset = Salon.objects.all()
    serializer_class = AdminSalonSerializer
    permission_classes = [IsManagementAdminOrStaff]

    def get_object(self):
        account_uid = self.kwargs.get("account_uid")
        salon_uid = self.kwargs.get("salon_uid")

        try:
            salon = Salon.objects.get(uid=salon_uid, account__uid=account_uid)
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
    filterset_fields = ["gender_specific", "category__name"]
    search_fields = ["name", "assign_employees__name", "assign_employees__employee_id"]
    ordering_fields = [
        "created_at",
        "name",
        "price",
        "discount_percentage",
        "service_duration",
    ]
    ordering = ["-created_at"]

    def get_queryset(self):
        account_uid = self.kwargs.get("account_uid")
        salon_uid = self.kwargs.get("salon_uid")

        try:
            salon = Salon.objects.get(uid=salon_uid, account__uid=account_uid)
            return Service.objects.filter(
                account__uid=account_uid, salon=salon
            ).order_by("created_at")
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
    filterset_fields = ["category__name"]
    search_fields = ["name"]
    ordering_fields = ["created_at", "name"]
    ordering = ["-created_at"]

    def get_queryset(self):
        account_uid = self.kwargs.get("account_uid")
        salon_uid = self.kwargs.get("salon_uid")

        try:
            salon = Salon.objects.get(uid=salon_uid, account__uid=account_uid)
            return Product.objects.filter(account__uid=account_uid, salon=salon)
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
    filterset_fields = ["designation__name"]
    search_fields = ["employee_id", "name"]
    ordering_fields = ["created_at", "name"]
    ordering = ["-created_at"]

    def get_queryset(self):
        account_uid = self.kwargs.get("account_uid")
        salon_uid = self.kwargs.get("salon_uid")

        try:
            salon = Salon.objects.get(uid=salon_uid, account__uid=account_uid)
            return Employee.objects.filter(account__uid=account_uid, salon=salon)
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
    filterset_fields = {
        "booking_date": ["gte", "lte"],
        "status": ["exact"],
    }
    search_fields = [
        "booking_id",
        "customer__first_name",
        "customer__last_name",
        "customer__phone",
        "customer__email",
        "chair__name",
        "employee__name",
        "employee__employee_id",
        "services__name",
        "products__name",
    ]
    ordering_fields = ["created_at", "booking_duration"]
    ordering = ["-created_at"]

    def get_queryset(self):
        account_uid = self.kwargs.get("account_uid")
        salon_uid = self.kwargs.get("salon_uid")

        try:
            salon = Salon.objects.get(uid=salon_uid, account__uid=account_uid)
            return Booking.objects.filter(account__uid=account_uid, salon=salon)
        except Salon.DoesNotExist:
            raise ValidationError("Salon not found.")


class AdminAccountEnquiryListView(ListAPIView):
    serializer_class = AdminAccountEnquirySerializer
    permission_classes = [IsManagementAdminOrStaff]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["level", "topic", "status"]
    search_fields = ["subject", "queries"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        account_uid = self.kwargs.get("account_uid")

        return SupportTicket.objects.filter(account__uid=account_uid)


class AdminAccountEnquiryDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = AdminAccountEnquirySerializer
    permission_classes = [IsManagementAdminOrStaff]

    def get_object(self):
        account_uid = self.kwargs.get("account_uid")
        uid = self.kwargs.get("account_enquiry_uid")

        return SupportTicket.objects.get(uid=uid, account__uid=account_uid)


class AdminSubscriptionPlanListView(ListCreateAPIView):
    serializer_class = AdminSubscriptionPlanSerializer
    pass

from datetime import datetime

from django.db.models import Prefetch, Count, Q

from rest_framework.generics import (
    ListAPIView,
    RetrieveAPIView,
    ListCreateAPIView,
    RetrieveUpdateAPIView,
    RetrieveUpdateDestroyAPIView,
    get_object_or_404,
)
from rest_framework.response import Response
from rest_framework import filters
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from apps.authentication.models import AccountMembership
from apps.salon.choices import BookingStatus, CustomerType
from apps.salon.models import (
    Booking,
    Chair,
    Salon,
    Service,
    Product,
    Employee,
    Customer,
)

from common.filters import SalonLeadFilter
from common.permissions import (
    IsOwner,
    IsOwnerOrAdmin,
    IsOwnerOrAdminOrStaff,
)

from ..serializers.salons import (
    SalonSerializer,
    SalonServiceSerializer,
    SalonProductSerializer,
    SalonChairSerializer,
    EmployeeSerializer,
    SalonChairBookingSerializer,
    SalonBookingCalendarSerializer,
    SalonBookingCalendarDetailSerializer,
    SalonLookBookSerializer,
    # SalonLeadSerializer,
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
        elif self.request.method == "DELETE":
            self.permission_classes = [IsOwner]
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

class SalonDashboardApiView(APIView):
    def get(self, request, salon_uid):
        user = request.user
        account = request.account

        counts = Salon.objects.filter(
            uid=salon_uid, account=account, account__members__user=user
        ).aggregate(
            total_chairs=Count('salon_chairs', distinct=True),
            total_employees=Count('salon_employees', distinct=True),
            total_services=Count('salon_services', distinct=True),
            total_products=Count('salon_products', distinct=True),
        )

        return Response(counts)

class SalonServiceListView(ListCreateAPIView):
    serializer_class = SalonServiceSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ["name", "category__name"]
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
    search_fields = ["name", "category__name"]
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
    serializer_class = EmployeeSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ["employee_id", "name", "phone", "designation__name"]
    ordering_fields = ["created_at"]
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

        return Employee.objects.filter(
            account=account,
            salon__uid=salon_uid,
            account__members__user=user,
        )

    def perform_create(self, serializer):
        account = self.request.account
        salon_uid = self.kwargs.get("salon_uid")
        salon = get_object_or_404(Salon, uid=salon_uid, account=account)
        serializer.save(salon=salon, account=account)


class SalonEmployeeDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = EmployeeSerializer
    lookup_field = "uid"
    lookup_url_kwarg = "employee_uid"

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
        employee_uid = self.kwargs.get("employee_uid")

        return get_object_or_404(
            Employee,
            uid=employee_uid,
            salon__uid=salon_uid,
            account=account,
            account__members__user=user,
        )


class SalonChairListView(ListCreateAPIView):
    serializer_class = SalonChairSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ["name", "type__name"]
    ordering_fields = ["created_at"]
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

        return Chair.objects.filter(
            account=account,
            salon__uid=salon_uid,
            account__members__user=user,
        )

    def perform_create(self, serializer):
        account = self.request.account
        salon_uid = self.kwargs.get("salon_uid")
        salon = get_object_or_404(Salon, uid=salon_uid, account=account)
        serializer.save(salon=salon, account=account)


class SalonChairDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = SalonChairSerializer
    lookup_field = "uid"
    lookup_url_kwarg = "chair_uid"

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
        chair_uid = self.kwargs.get("chair_uid")

        return get_object_or_404(
            Chair,
            uid=chair_uid,
            salon__uid=salon_uid,
            account=account,
            account__members__user=user,
        )


class SalonChairBookingListView(ListCreateAPIView):
    serializer_class = SalonChairBookingSerializer
    permission_classes = [IsOwnerOrAdminOrStaff]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    search_fields = [
        "customer__first_name",
        "customer__last_name",
        "customer__email",
        "customer__phone",
        "employee__name",
        "booking_id",
    ]
    filterset_fields = {
        "booking_date": ["exact", "gte", "lte"],
        "status": ["exact"],
    }
    ordering_fields = ["created_at", "booking_date", "booking_time"]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user
        account = self.request.account
        salon_uid = self.kwargs.get("salon_uid")
        chair_uid = self.kwargs.get("chair_uid")

        return Booking.objects.filter(
            account=account,
            chair__uid=chair_uid,
            salon__uid=salon_uid,
            account__members__user=user,
        )

    def perform_create(self, serializer):
        account = self.request.account
        salon_uid = self.kwargs.get("salon_uid")
        chair_uid = self.kwargs.get("chair_uid")
        salon = get_object_or_404(Salon, uid=salon_uid, account=account)
        chair = get_object_or_404(Chair, uid=chair_uid, salon=salon)
        serializer.save(salon=salon, chair=chair, account=account)


class SalonChairBookingDetailView(RetrieveUpdateAPIView):
    serializer_class = SalonChairBookingSerializer
    permission_classes = [IsOwnerOrAdminOrStaff]
    lookup_field = "uid"
    lookup_url_kwarg = "booking_uid"

    def get_object(self):
        user = self.request.user
        account = self.request.account
        salon_uid = self.kwargs.get("salon_uid")
        chair_uid = self.kwargs.get("chair_uid")
        booking_uid = self.kwargs.get("booking_uid")

        return get_object_or_404(
            Booking,
            uid=booking_uid,
            chair__uid=chair_uid,
            salon__uid=salon_uid,
            account=account,
            account__members__user=user,
        )

    def perform_update(self, serializer):
        account = self.request.account
        salon_uid = self.kwargs.get("salon_uid")
        chair_uid = self.kwargs.get("chair_uid")
        salon = get_object_or_404(Salon, uid=salon_uid, account=account)
        chair = get_object_or_404(Chair, uid=chair_uid, salon=salon, account=account)
        serializer.save(salon=salon, chair=chair, account=account)


class SalonBookingCalendarListView(ListAPIView):
    serializer_class = SalonBookingCalendarSerializer
    permission_classes = [IsOwnerOrAdminOrStaff]

    def get_queryset(self):
        user = self.request.user
        account = self.request.account
        salon_uid = self.kwargs.get("salon_uid")

        # Get date from query params, default to today
        date_str = self.request.query_params.get("date")
        status = self.request.query_params.get("status")

        if date_str:
            try:
                target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                target_date = datetime.now().date()
        else:
            target_date = datetime.now().date()

        allowed_statuses = [
            BookingStatus.PLACED,
            BookingStatus.INPROGRESS,
            BookingStatus.RESCHEDULED,
            BookingStatus.COMPLETED,
            BookingStatus.CANCELLED,
            BookingStatus.ABSENT,
        ]

        # If status is invalid, ignore it (don’t filter by status)
        if status not in allowed_statuses:
            status = None

        # Build the booking queryset
        booking_qs = Booking.objects.filter(
            account=account,
            salon__uid=salon_uid,
            booking_date=target_date,
        )
        if status:
            booking_qs = booking_qs.filter(status=status)

        # Return employees with prefetch of filtered bookings
        return Employee.objects.filter(
            salon__uid=salon_uid,
            account=account,
            account__members__user=user,
        ).prefetch_related(Prefetch("employee_bookings", queryset=booking_qs))


class SalonBookingCalendarDetailView(RetrieveUpdateAPIView):
    serializer_class = SalonBookingCalendarDetailSerializer
    lookup_field = "uid"
    lookup_url_kwarg = "booking_uid"

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH"]:
            self.permission_classes = [IsOwnerOrAdmin]
        else:
            self.permission_classes = [IsOwnerOrAdminOrStaff]

        return super().get_permissions()

    def get_object(self):
        user = self.request.user
        account = self.request.account
        salon_uid = self.kwargs.get("salon_uid")
        booking_uid = self.kwargs.get("booking_uid")

        return get_object_or_404(
            Booking,
            uid=booking_uid,
            salon__uid=salon_uid,
            account=account,
            account__members__user=user,
        )


class SalonLookBookListView(ListAPIView):
    serializer_class = SalonLookBookSerializer
    permission_classes = [IsOwnerOrAdminOrStaff]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = [
        "customer__first_name",
        "customer__last_name",
        "customer__email",
        "customer__phone",
        "booking_id",
    ]
    ordering_fields = ["created_at", "booking_date"]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user
        account = self.request.account
        salon_uid = self.kwargs.get("salon_uid")

        queryset = Booking.objects.filter(
            account=account,
            salon__uid=salon_uid,
            account__members__user=user,
            status=BookingStatus.COMPLETED,
        )

        return queryset


class SalonLookBookDetailView(RetrieveUpdateAPIView):
    serializer_class = SalonLookBookSerializer
    lookup_field = "uid"
    lookup_url_kwarg = "lookbook_uid"

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH"]:
            self.permission_classes = [IsOwnerOrAdmin]
        else:
            self.permission_classes = [IsOwnerOrAdminOrStaff]

        return super().get_permissions()

    def get_object(self):
        user = self.request.user
        account = self.request.account
        salon_uid = self.kwargs.get("salon_uid")
        lookbook_uid = self.kwargs.get("lookbook_uid")

        return get_object_or_404(
            Booking,
            uid=lookbook_uid,
            salon__uid=salon_uid,
            account=account,
            account__members__user=user,
            status=BookingStatus.COMPLETED,
        )


# # TODO: Remove it later
# class SalonLeadListView(ListCreateAPIView):
#     serializer_class = SalonLeadSerializer
#     permission_classes = [IsOwnerOrAdminOrStaff]
#     filter_backends = [
#         DjangoFilterBackend,
#         filters.SearchFilter,
#         filters.OrderingFilter,
#     ]
#     filterset_class = SalonLeadFilter
#     search_fields = [
#         "first_name",
#         "last_name",
#         "phone",
#         "email",
#         "source__name",
#     ]
#     ordering_fields = ["created_at"]
#     ordering = ["-created_at"]

#     def get_queryset(self):
#         user = self.request.user
#         account = self.request.account
#         salon_uid = self.kwargs.get("salon_uid")

#         return Customer.objects.filter(
#             account=account,
#             salon__uid=salon_uid,
#             account__members__user=user,
#             type=CustomerType.LEAD,
#         )

#     def perform_create(self, serializer):
#         account = self.request.account
#         salon_uid = self.kwargs.get("salon_uid")

#         salon = get_object_or_404(Salon, uid=salon_uid)

#         serializer.save(account=account, salon=salon)


# # TODO: Remove it later
# class SalonLeadDetailView(RetrieveUpdateAPIView):
#     serializer_class = SalonLeadSerializer
#     lookup_url_kwarg = "lead_uid"

#     def get_permissions(self):
#         if self.request.method in ["PUT", "PATCH"]:
#             self.permission_classes = [IsOwnerOrAdmin]
#         else:
#             self.permission_classes = [IsOwnerOrAdminOrStaff]

#         return super().get_permissions()

#     def get_object(self):
#         lead_uid = self.kwargs.get("lead_uid")

#         return get_object_or_404(
#             Customer,
#             uid=lead_uid,
#         )

from calendar import monthrange
from datetime import datetime
from datetime import timedelta
from decimal import Decimal
from decouple import config

# Register whatsapp sender on Twilio
from twilio.rest import Client
from twilio.rest.messaging.v2 import ChannelsSenderList

from django.db import transaction
from django.db.models import Prefetch, Count, Sum, F, DecimalField, Q
from django.db.models.functions import ExtractWeekDay, ExtractHour
from django.http import FileResponse
from django.utils import timezone

from rest_framework.generics import (
    ListAPIView,
    ListCreateAPIView,
    RetrieveUpdateAPIView,
    RetrieveUpdateDestroyAPIView,
    get_object_or_404,
)
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import filters, status
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend


from apps.authentication.models import AccountMembership
from apps.salon.choices import BookingStatus
from apps.salon.models import (
    Booking,
    Chair,
    Salon,
    Service,
    Product,
    Employee,
)

from apps.thirdparty.models import TwilioConfig
from apps.thirdparty.utils import create_twilio_subaccount

from common.crypto import encrypt_data, decrypt_data
from common.filters import BookingDateFilter
from common.permissions import (
    IsOwner,
    IsOwnerOrAdmin,
    IsOwnerOrAdminOrStaff,
)
from common.utils import generate_receipt_pdf


from ..serializers.salons import (
    SalonSerializer,
    SalonServiceSerializer,
    SalonProductSerializer,
    SalonChairSerializer,
    EmployeeSerializer,
    SalonBookingSerializer,
    SalonChairBookingSerializer,
    SalonBookingCalendarSerializer,
    SalonBookingCalendarDetailSerializer,
    SalonLookBookSerializer,
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
            total_chairs=Count("salon_chairs", distinct=True),
            total_employees=Count("salon_employees", distinct=True),
            total_services=Count("salon_services", distinct=True),
            total_products=Count("salon_products", distinct=True),
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


class SalonBookingListView(ListCreateAPIView):
    serializer_class = SalonBookingSerializer
    permission_classes = [IsOwnerOrAdminOrStaff]
    pagination_class = None

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filterset_class = BookingDateFilter

    search_fields = [
        "customer__first_name",
        "customer__last_name",
        "customer__email",
        "customer__phone",
        "booking_id",
    ]

    ordering_fields = ["created_at", "booking_date", "booking_time"]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user
        account = self.request.account
        salon_uid = self.kwargs.get("salon_uid")

        return Booking.objects.filter(
            account=account,
            salon__uid=salon_uid,
            account__members__user=user,
        )

    def perform_create(self, serializer):
        account = self.request.account
        salon_uid = self.kwargs.get("salon_uid")
        salon = get_object_or_404(Salon, uid=salon_uid, account=account)
        serializer.save(salon=salon, account=account)


class SalonBookingDetailView(RetrieveUpdateAPIView):
    serializer_class = SalonBookingSerializer
    permission_classes = [IsOwnerOrAdminOrStaff]
    lookup_field = "uid"
    lookup_url_kwarg = "booking_uid"

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

    def perform_update(self, serializer):
        account = self.request.account
        salon_uid = self.kwargs.get("salon_uid")
        salon = get_object_or_404(Salon, uid=salon_uid, account=account)
        serializer.save(salon=salon, account=account)


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


class SalonBookingReceiptDownloadAPIView(APIView):
    permission_classes = [IsOwnerOrAdminOrStaff]

    def get(self, request, salon_uid, booking_uid, *args, **kwargs):
        try:
            account = request.account
            booking = Booking.objects.get(
                uid=booking_uid, account=account, salon__uid=salon_uid
            )
        except Booking.DoesNotExist:
            return Response({"detail": "Booking not found"}, status=404)

        if booking.status != BookingStatus.COMPLETED:
            return Response(
                {"detail": "Receipt is only available for completed bookings."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            pdf_file = generate_receipt_pdf(booking)
        except Exception as e:
            return Response(
                {"detail": f"Error generating receipt: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        filename = f"receipt_{booking.booking_id}.pdf"

        return FileResponse(
            pdf_file,
            as_attachment=True,
            filename=filename,
            content_type="application/pdf",
        )


class BaseRevenueAnalyticsView(generics.GenericAPIView):
    """Base view for revenue analytics with time filtering"""

    permission_classes = [IsOwnerOrAdminOrStaff]

    def get_date_range(self, period):
        """Calculate date range based on period filter"""
        today = timezone.now().date()

        if period == "this_week":
            start_date = today - timedelta(days=today.weekday())
            end_date = today
        elif period == "last_week":
            start_date = today - timedelta(days=today.weekday() + 7)
            end_date = start_date + timedelta(days=6)
        elif period == "this_month":
            start_date = today.replace(day=1)
            end_date = today
        elif period == "last_6_months":
            start_date = today - timedelta(days=180)
            end_date = today
        elif period == "last_year":
            start_date = today - timedelta(days=365)
            end_date = today
        else:
            start_date = None
            end_date = None

        return start_date, end_date

    def get_completed_bookings_queryset(self, start_date, end_date):
        salon_uid = self.kwargs.get("salon_uid")
        salon = get_object_or_404(Salon, uid=salon_uid, account=self.request.account)

        qs = Booking.objects.filter(
            status=BookingStatus.COMPLETED,
            salon=salon,
            account=self.request.account,
        )

        if start_date and end_date:
            qs = qs.filter(
                booking_date__gte=start_date,
                booking_date__lte=end_date,
            )

        return qs


class TopServiceCategoryRevenueView(BaseRevenueAnalyticsView):
    def get(self, request, *args, **kwargs):
        period = request.query_params.get("period", "all_time")
        start_date, end_date = self.get_date_range(period)

        bookings = self.get_completed_bookings_queryset(start_date, end_date)

        category_revenue = (
            bookings.values("services__category__name")
            .annotate(
                revenue=Sum(
                    F("services__price")
                    * (1 - F("services__discount_percentage") / 100),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                )
            )
            .filter(revenue__gt=0)
            .order_by("-revenue")[:5]
        )

        data = [
            {
                "service_category": item["services__category__name"],
                "revenue": float(item["revenue"]),
            }
            for item in category_revenue
        ]

        return Response(data)


class TopProductCategoryRevenueView(BaseRevenueAnalyticsView):
    """
    GET /api/analytics/revenue/product-categories/
    GET /api/analytics/revenue/product-categories/?period=this_month
    Returns top 5 product categories by revenue
    """

    def get(self, request, *args, **kwargs):
        period = request.query_params.get("period", "all_time")
        start_date, end_date = self.get_date_range(period)

        bookings = self.get_completed_bookings_queryset(start_date, end_date)

        category_revenue = (
            bookings.values("products__category__name")
            .annotate(
                revenue=Sum(
                    "products__price",
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                )
            )
            .filter(revenue__gt=0)
            .order_by("-revenue")[:5]
        )

        data = [
            {
                "product_category": item["products__category__name"],
                "revenue": float(item["revenue"]),
            }
            for item in category_revenue
        ]

        return Response(data)


class TopServicesRevenueView(BaseRevenueAnalyticsView):
    """
    GET /api/analytics/revenue/services/
    GET /api/analytics/revenue/services/?period=last_6_months
    Returns top 5 individual services by revenue
    """

    def get(self, request, *args, **kwargs):
        period = request.query_params.get("period", "all_time")
        start_date, end_date = self.get_date_range(period)

        bookings = self.get_completed_bookings_queryset(start_date, end_date)

        service_revenue = (
            bookings.values("services__name")
            .annotate(
                revenue=Sum(
                    F("services__price")
                    * (1 - F("services__discount_percentage") / 100),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                )
            )
            .filter(revenue__gt=0)
            .order_by("-revenue")[:5]
        )

        data = [
            {
                "service_name": item["services__name"],
                "revenue": float(item["revenue"]),
            }
            for item in service_revenue
        ]

        return Response(data)


class TopProductsRevenueView(BaseRevenueAnalyticsView):
    """
    GET /api/analytics/revenue/products/
    GET /api/analytics/revenue/products/?period=last_year
    Returns top 5 individual products by revenue
    """

    def get(self, request, *args, **kwargs):
        period = request.query_params.get("period", "all_time")
        start_date, end_date = self.get_date_range(period)

        bookings = self.get_completed_bookings_queryset(start_date, end_date)

        product_revenue = (
            bookings.values("products__name")
            .annotate(
                revenue=Sum(
                    "products__price",
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                )
            )
            .filter(revenue__gt=0)
            .order_by("-revenue")[:5]
        )

        data = [
            {
                "product_name": item["products__name"],
                "revenue": float(item["revenue"]),
            }
            for item in product_revenue
        ]

        return Response(data)


class BookingsByMonthView(APIView):
    permission_classes = [IsOwnerOrAdminOrStaff]

    def get(self, request, salon_uid):
        # Get query parameters

        account = request.account
        salon = get_object_or_404(Salon, uid=salon_uid, account=account)

        month = request.query_params.get("month")
        year = request.query_params.get("year")

        if not month or not year:
            return Response(
                {"error": "Both 'month' and 'year' query parameters are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            month = int(month)
            year = int(year)

            if month < 1 or month > 12:
                raise ValueError("Month must be between 1 and 12")

            if year < 2000 or year > 2100:
                raise ValueError("Year must be between 2000 and 2100")

        except ValueError as e:
            return Response(
                {"error": f"Invalid month or year: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get the number of days in the selected month
        _, days_in_month = monthrange(year, month)

        # Build query filters
        filters = Q(
            account=account,
            salon=salon,
            status=BookingStatus.COMPLETED,
            booking_date__year=year,
            booking_date__month=month,
        )

        # Query completed bookings for the selected month
        bookings = (
            Booking.objects.filter(filters)
            .values("booking_date")
            .annotate(count=Count("id"))
            .order_by("booking_date")
        )

        # Initialize all dates with 0 bookings
        bookings_by_date = {day: 0 for day in range(1, days_in_month + 1)}

        # Fill in actual booking counts
        for booking in bookings:
            day = booking["booking_date"].day
            bookings_by_date[day] = booking["count"]

        # Get month name
        month_name = datetime(year, month, 1).strftime("%B")

        # Format response as dictionary with day as key and count as value
        response_data = {
            str(day): bookings_by_date[day] for day in range(1, days_in_month + 1)
        }

        return Response(response_data, status=status.HTTP_200_OK)


class PeakHoursAnalyticsView(APIView):
    permission_classes = [IsOwnerOrAdminOrStaff]

    def get(self, request, salon_uid):
        account = request.account
        salon = get_object_or_404(Salon, uid=salon_uid, account=account)

        filter_type = request.query_params.get("period", "all_time")

        # Validate filter type
        valid_filters = ["today", "last_7_days", "all_time"]
        if filter_type not in valid_filters:
            return Response(
                {"error": f"Invalid filter. Use one of: {', '.join(valid_filters)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Define date filters
        today = datetime.now().date()

        if filter_type == "today":
            date_filter = Q(booking_date=today)
        elif filter_type == "last_7_days":
            date_filter = Q(booking_date__gte=today - timedelta(days=7))
        else:  # all_time
            date_filter = Q()

        # Build query filters
        filters = (
            Q(account=account, salon=salon, status=BookingStatus.COMPLETED)
            & date_filter
        )

        # Query completed bookings and extract hour
        bookings = (
            Booking.objects.filter(filters)
            .annotate(hour=ExtractHour("booking_time"))
            .values("hour")
            .annotate(count=Count("id"))
            .order_by("hour")
        )

        # Define 2-hour ranges for typical salon hours (9 AM - 9 PM)
        hour_ranges = {
            "09:00-11:00": 0,
            "11:00-13:00": 0,
            "13:00-15:00": 0,
            "15:00-17:00": 0,
            "17:00-19:00": 0,
            "19:00-21:00": 0,
        }

        # Map hours to ranges
        for booking in bookings:
            hour = booking["hour"]
            count = booking["count"]

            if 9 <= hour < 11:
                hour_ranges["09:00-11:00"] += count
            elif 11 <= hour < 13:
                hour_ranges["11:00-13:00"] += count
            elif 13 <= hour < 15:
                hour_ranges["13:00-15:00"] += count
            elif 15 <= hour < 17:
                hour_ranges["15:00-17:00"] += count
            elif 17 <= hour < 19:
                hour_ranges["17:00-19:00"] += count
            elif 19 <= hour < 21:
                hour_ranges["19:00-21:00"] += count

        return Response(hour_ranges, status=status.HTTP_200_OK)


class PeakDaysAnalyticsView(APIView):
    permission_classes = [IsOwnerOrAdminOrStaff]

    def get(self, request, salon_uid):
        account = request.account
        salon = get_object_or_404(Salon, uid=salon_uid, account=account)

        filter_type = request.query_params.get("period", "this_week")

        # Validate filter type
        valid_filters = ["this_week", "last_week", "all_time"]
        if filter_type not in valid_filters:
            return Response(
                {"error": f"Invalid filter. Use one of: {', '.join(valid_filters)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Define date filters
        today = datetime.now().date()

        # Get the start of this week (Monday)
        days_since_monday = today.weekday()
        this_week_start = today - timedelta(days=days_since_monday)
        this_week_end = this_week_start + timedelta(days=6)

        if filter_type == "this_week":
            date_filter = Q(
                booking_date__gte=this_week_start, booking_date__lte=this_week_end
            )
        elif filter_type == "last_week":
            last_week_start = this_week_start - timedelta(days=7)
            last_week_end = this_week_start - timedelta(days=1)
            date_filter = Q(
                booking_date__gte=last_week_start, booking_date__lte=last_week_end
            )
        else:  # all_time
            date_filter = Q()

        # Build query filters
        filters = (
            Q(account=account, salon=salon, status=BookingStatus.COMPLETED)
            & date_filter
        )

        # Query completed bookings and extract weekday
        bookings = (
            Booking.objects.filter(filters)
            .annotate(weekday=ExtractWeekDay("booking_date"))
            .values("weekday")
            .annotate(count=Count("id"))
            .order_by("weekday")
        )

        # Map weekday numbers to names
        # ExtractWeekDay: Sunday=1, Monday=2, Tuesday=3, ..., Saturday=7
        weekday_mapping = {
            2: "Monday",
            3: "Tuesday",
            4: "Wednesday",
            5: "Thursday",
            6: "Friday",
            7: "Saturday",
            1: "Sunday",
        }

        # Initialize all days with 0
        days_data = {
            "Monday": 0,
            "Tuesday": 0,
            "Wednesday": 0,
            "Thursday": 0,
            "Friday": 0,
            "Saturday": 0,
            "Sunday": 0,
        }

        # Fill in actual booking counts
        for booking in bookings:
            day_name = weekday_mapping[booking["weekday"]]
            days_data[day_name] = booking["count"]

        # Maintain Monday-Sunday order
        ordered_days = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]

        # Format response for bar chart
        response_data = {day: days_data[day] for day in ordered_days}

        return Response(response_data, status=status.HTTP_200_OK)


class CustomerAnalysisApiView(APIView):
    permission_classes = [IsOwnerOrAdminOrStaff]

    def get(self, request, salon_uid, *args, **kwargs):
        account = request.account
        salon = get_object_or_404(Salon, uid=salon_uid, account=account)

        # Get time period from query params (default: 'all_time')
        period = request.query_params.get("period", "all_time")

        # Calculate date ranges
        now = timezone.now()
        today = now.date()

        if period == "this_week":
            start_date = today - timedelta(days=today.weekday())  # Monday
            end_date = today
        elif period == "last_week":
            start_date = today - timedelta(days=today.weekday() + 7)
            end_date = start_date + timedelta(days=6)
        elif period == "this_month":
            start_date = today.replace(day=1)
            end_date = today
        elif period == "all_time":
            start_date = None
            end_date = None
        else:
            return Response(
                {
                    "error": "Invalid period. Use: this_week, last_week, this_month, or all_time"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Base queryset - filter completed bookings
        bookings = Booking.objects.filter(
            salon=salon, account=account, status=BookingStatus.COMPLETED
        )

        # Apply date filter if not all_time
        if start_date and end_date:
            bookings = bookings.filter(
                booking_date__gte=start_date, booking_date__lte=end_date
            )

        # Get all unique customers who had bookings in this period
        customers_in_period = bookings.values_list("customer_id", flat=True).distinct()

        # For each customer, check if they had any completed bookings BEFORE this period
        new_customers = []
        repeated_customers = []

        for customer_id in customers_in_period:
            # Check if customer had any completed bookings before this period
            if start_date:
                # For specific time periods, check bookings before start_date
                previous_bookings = Booking.objects.filter(
                    salon=salon,
                    account=account,
                    customer_id=customer_id,
                    status=BookingStatus.COMPLETED,
                    booking_date__lt=start_date,
                ).exists()
            else:
                # For 'all_time', we consider the first booking
                # Get customer's first completed booking
                first_booking = (
                    Booking.objects.filter(
                        salon=salon,
                        account=account,
                        customer_id=customer_id,
                        status=BookingStatus.COMPLETED,
                    )
                    .order_by("booking_date", "booking_time")
                    .first()
                )

                # Check if customer has more than one booking
                previous_bookings = (
                    Booking.objects.filter(
                        salon=salon,
                        account=account,
                        customer_id=customer_id,
                        status=BookingStatus.COMPLETED,
                    ).count()
                    > 1
                )

            if previous_bookings:
                repeated_customers.append(customer_id)
            else:
                new_customers.append(customer_id)

        # Count bookings for each category
        new_customer_booking_count = bookings.filter(
            customer_id__in=new_customers
        ).count()

        repeated_customer_booking_count = bookings.filter(
            customer_id__in=repeated_customers
        ).count()

        total_bookings = new_customer_booking_count + repeated_customer_booking_count

        return Response(
            {
                "total_bookings": total_bookings,
                "new_customer_booking_count": new_customer_booking_count,
                "repeated_customer_booking_count": repeated_customer_booking_count,
            }
        )


class TopEmployeeApiView(APIView):
    permission_classes = [IsOwnerOrAdminOrStaff]

    def get(self, request, salon_uid, *args, **kwargs):
        account = request.account
        salon = get_object_or_404(Salon, uid=salon_uid, account=account)

        bookings = Booking.objects.filter(
            status=BookingStatus.COMPLETED,
            salon=salon,
            account=account,
        )

        # Get top 5 employees by calculating revenue
        top_employees = (
            Employee.objects.filter(employee_bookings__in=bookings)
            .annotate(
                # Count number of bookings this employee handled
                booking_count=Count("employee_bookings", distinct=True),
                # Calculate total revenue from bookings handled by this employee
                total_revenue=Sum(
                    F("employee_bookings__services__price")
                    * (1 - F("employee_bookings__services__discount_percentage") / 100),
                    output_field=DecimalField(max_digits=10, decimal_places=2),
                ),
            )
            .order_by("-total_revenue")[:5]
        )

        return Response(
            [
                {
                    "employee_id": employee.id,
                    "name": employee.name,
                    "designation": (
                        employee.designation.name if employee.designation else ""
                    ),
                    "total_revenue": float(employee.total_revenue or Decimal("0.00")),
                }
                for employee in top_employees
            ]
        )


class TopSellingServiceApiView(APIView):
    permission_classes = [IsOwnerOrAdminOrStaff]

    def get(self, request, salon_uid, *args, **kwargs):
        account = request.account
        salon = get_object_or_404(Salon, uid=salon_uid, account=account)

        period = request.query_params.get("period", "all_time")

        # Calculate date range
        now = timezone.now()
        today = now.date()

        if period == "this_week":
            start_date = today - timedelta(days=today.weekday())
            end_date = today
        elif period == "last_week":
            start_date = today - timedelta(days=today.weekday() + 7)
            end_date = start_date + timedelta(days=6)
        elif period == "this_month":
            start_date = today.replace(day=1)
            end_date = today
        elif period == "all_time":
            start_date = None
            end_date = None
        else:
            return Response(
                {
                    "error": "Invalid period. Use: this_week, last_week, this_month, or all_time"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        bookings = Booking.objects.filter(
            status=BookingStatus.COMPLETED,
            salon=salon,
            account=account,
        )

        if start_date and end_date:
            bookings = bookings.filter(
                booking_date__gte=start_date, booking_date__lte=end_date
            )

        # Get top 5 services by calculating revenue
        top_services = (
            Service.objects.filter(service_bookings__in=bookings)
            .annotate(
                # Count number of bookings this service appears in
                booking_count=Count("service_bookings", distinct=True),
                # Calculate total revenue (price * number of bookings)
                total_revenue=Sum(
                    F("price") * (1 - F("discount_percentage") / 100),
                    output_field=DecimalField(max_digits=10, decimal_places=2),
                ),
            )
            .order_by("-total_revenue")[:5]
        )

        return Response(
            [
                {
                    "name": service.name,
                    "description": service.description,
                    "total_revenue": float(service.total_revenue or Decimal("0.00")),
                }
                for service in top_services
            ]
        )


class TopSellingProductApiView(APIView):
    permission_classes = [IsOwnerOrAdminOrStaff]

    def get(self, request, salon_uid, *args, **kwargs):
        account = request.account
        salon = get_object_or_404(Salon, uid=salon_uid, account=account)

        period = request.query_params.get("period", "all_time")

        # Calculate date range
        now = timezone.now()
        today = now.date()

        if period == "this_week":
            start_date = today - timedelta(days=today.weekday())  # Monday
            end_date = today
        elif period == "last_week":
            start_date = today - timedelta(days=today.weekday() + 7)
            end_date = start_date + timedelta(days=6)
        elif period == "this_month":
            start_date = today.replace(day=1)
            end_date = today
        elif period == "all_time":
            start_date = None
            end_date = None
        else:
            return Response(
                {
                    "error": "Invalid period. Use: this_week, last_week, this_month, or all_time"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        bookings = Booking.objects.filter(
            status=BookingStatus.COMPLETED,
            salon=salon,
            account=account,
        )

        if start_date and end_date:
            bookings = bookings.filter(
                booking_date__gte=start_date, booking_date__lte=end_date
            )

        # Get top 5 products by calculating revenue
        top_products = (
            Product.objects.filter(product_bookings__in=bookings)
            .annotate(
                # Count number of bookings this product appears in
                booking_count=Count("product_bookings", distinct=True),
                # Calculate total revenue (price * number of bookings)
                total_revenue=Sum(
                    F("price"),
                    output_field=DecimalField(max_digits=10, decimal_places=2),
                ),
            )
            .order_by("-total_revenue")[:5]
        )

        return Response(
            [
                {
                    "name": product.name,
                    "description": product.description,
                    "total_revenue": float(product.total_revenue or Decimal("0.00")),
                }
                for product in top_products
            ]
        )


class SalonWhatsappView(APIView):
    """
    Receives Embedded Signup result from frontend and registers the sender with Twilio.
    """

    permission_classes = []

    def get(self, request, salon_uid, *args, **kwargs):
        account = request.account
        salon = get_object_or_404(Salon, uid=salon_uid, account=account)

        twilio_config = TwilioConfig.objects.filter(
            salon=salon, account=account
        ).first()

        if not twilio_config:
            return Response(
                {"error": "No WhatsApp sender registered for this salon"},
                status=status.HTTP_404_NOT_FOUND,
            )

        whatsapp_sender_number = twilio_config.whatsapp_sender_number

        return Response(
            {
                "salon": salon.name,
                "whatsapp_sender_number": whatsapp_sender_number,
                "sender_status": twilio_config.sender_status,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request, salon_uid, *args, **kwargs):

        with transaction.atomic():
            print("------------------------------->", request.data)
            whatsapp_sender_number = request.data.get("whatsapp_sender_number")

            if not whatsapp_sender_number:
                return Response(
                    {"error": "Missing whatsapp_sender_number"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Create a subaccount for the salon
            account = request.account
            salon = get_object_or_404(Salon, uid=salon_uid, account=account)
            meta_config = account.account_meta_config

            crypto_password = config("CRYPTO_PASSWORD")
            auth_token = decrypt_data(meta_config.auth_token, crypto_password)
            account_sid = decrypt_data(meta_config.account_sid, crypto_password)
            waba_id = decrypt_data(meta_config.waba_id, crypto_password)

            print("-------------------------------> Account SID:", account_sid)
            print("-------------------------------> Auth Token:", auth_token)
            print("-------------------------------> WABA ID:", waba_id)

            client = Client(account_sid, auth_token)
            # client = Client(account_sid, auth_token)
            sender = client.messaging.v2.channels_senders.create(
                messaging_v2_channels_sender_requests_create=ChannelsSenderList.MessagingV2ChannelsSenderRequestsCreate(
                    {
                        "sender_id": f"whatsapp:{whatsapp_sender_number}",
                        "configuration": ChannelsSenderList.MessagingV2ChannelsSenderConfiguration(
                            {
                                "waba_id": waba_id,
                            }
                        ),
                        "profile": ChannelsSenderList.MessagingV2ChannelsSenderProfile(
                            {"name": salon.name[:64]}
                        ),
                        "webhook": ChannelsSenderList.MessagingV2ChannelsSenderWebhook(
                            {
                                "callback_url": "https://api.afrobeutic.com/webhooks/whatsapp-callback",
                                "callback_method": "POST",
                                "fallback_url": "https://api.afrobeutic.com/webhooks/whatsapp-fallback",
                                "fallback_method": "POST",
                                "status_callback_url": "https://api.afrobeutic.com/webhooks/whatsapp-callback-status",
                                "status_callback_method": "POST",
                            }
                        ),
                    }
                )
            )

            # # Store credentials in the database
            encrypt_sender_sid = encrypt_data(sender.sid, crypto_password)

            twilio_config = TwilioConfig.objects.create(
                sender_sid=encrypt_sender_sid,
                whatsapp_sender_number=f"whatsapp:{whatsapp_sender_number}",
                sender_status=sender.status,
                salon=salon,
                account=account,
            )
            print("-------------------------------> Subaccount created:", twilio_config)

            return Response(
                {
                    "message": "WhatsApp sender registered successfully",
                    "salon": salon.name,
                    "sender_status": sender.status,
                },
                status=status.HTTP_201_CREATED,
            )

    def delete(self, request, salon_uid):
        with transaction.atomic():
            account = request.account
            salon = get_object_or_404(Salon, uid=salon_uid, account=account)

            meta_config = account.account_meta_config
            account_sid = decrypt_data(
                meta_config.account_sid, config("CRYPTO_PASSWORD")
            )
            auth_token = decrypt_data(meta_config.auth_token, config("CRYPTO_PASSWORD"))

            twilio_config = get_object_or_404(
                TwilioConfig, salon=salon, account=account
            )
            sender_sid = decrypt_data(
                twilio_config.sender_sid, config("CRYPTO_PASSWORD")
            )
            client = Client(account_sid, auth_token)

            client.messaging.v2.channels_senders(sender_sid).delete()
            twilio_config.delete()

            return Response(
                {"message": "WhatsApp configuration deleted successfully"},
                status=status.HTTP_204_NO_CONTENT,
            )

from datetime import datetime
from datetime import timedelta
from decimal import Decimal

from django.db.models import Prefetch, Count, Sum, F, DecimalField, Q
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
            # Default to this month
            start_date = today.replace(day=1)
            end_date = today

        return start_date, end_date

    def get_completed_bookings_queryset(self, start_date, end_date):
        """Get completed bookings within date range"""

        salon_uid = self.kwargs.get("salon_uid")
        salon = get_object_or_404(Salon, uid=salon_uid, account=self.request.account)

        return Booking.objects.filter(
            status=BookingStatus.COMPLETED,
            booking_date__gte=start_date,
            booking_date__lte=end_date,
            salon=salon,
            account=self.request.account,
        )


class TopServiceCategoryRevenueView(BaseRevenueAnalyticsView):
    """
    GET /api/analytics/revenue/service-categories/?period=this_week
    Returns top 5 service categories by revenue
    """

    def get(self, request, *args, **kwargs):
        period = request.query_params.get("period", "this_month")
        start_date, end_date = self.get_date_range(period)

        bookings = self.get_completed_bookings_queryset(start_date, end_date)

        # Calculate revenue per service category
        category_revenue = (
            bookings.values("services__category__uid", "services__category__name")
            .annotate(
                total_revenue=Sum(
                    F("services__price")
                    * (1 - F("services__discount_percentage") / 100),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                )
            )
            .filter(total_revenue__gt=0)
            .order_by("-total_revenue")[:5]
        )

        # Format response for pie chart
        data = []
        total = Decimal("0.00")

        for item in category_revenue:
            revenue = item["total_revenue"] or Decimal("0.00")
            total += revenue
            data.append(
                {
                    "category_uid": item["services__category__uid"],
                    "category_name": item["services__category__name"],
                    "revenue": float(revenue),
                }
            )

        # Add percentages
        for item in data:
            item["percentage"] = (
                round((Decimal(str(item["revenue"])) / total * 100), 2)
                if total > 0
                else 0
            )

        return Response(
            {
                "period": period,
                "start_date": start_date,
                "end_date": end_date,
                "total_revenue": float(total),
                "data": data,
            }
        )


class TopProductCategoryRevenueView(BaseRevenueAnalyticsView):
    """
    GET /api/analytics/revenue/product-categories/?period=this_month
    Returns top 5 product categories by revenue
    """

    def get(self, request, *args, **kwargs):
        period = request.query_params.get("period", "this_month")
        start_date, end_date = self.get_date_range(period)

        bookings = self.get_completed_bookings_queryset(start_date, end_date)

        # Calculate revenue per product category
        category_revenue = (
            bookings.values("products__category__uid", "products__category__name")
            .annotate(
                total_revenue=Sum(
                    "products__price",
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                )
            )
            .filter(total_revenue__gt=0)
            .order_by("-total_revenue")[:5]
        )

        # Format response for pie chart
        data = []
        total = Decimal("0.00")

        for item in category_revenue:
            revenue = item["total_revenue"] or Decimal("0.00")
            total += revenue
            data.append(
                {
                    "category_uid": item["products__category__uid"],
                    "category_name": item["products__category__name"],
                    "revenue": float(revenue),
                }
            )

        # Add percentages
        for item in data:
            item["percentage"] = (
                round((Decimal(str(item["revenue"])) / total * 100), 2)
                if total > 0
                else 0
            )

        return Response(
            {
                "period": period,
                "start_date": start_date,
                "end_date": end_date,
                "total_revenue": float(total),
                "data": data,
            }
        )


class TopServicesRevenueView(BaseRevenueAnalyticsView):
    """
    GET /api/analytics/revenue/services/?period=last_6_months
    Returns top 5 individual services by revenue (Line chart data)
    """

    def get(self, request, *args, **kwargs):
        period = request.query_params.get("period", "this_month")
        start_date, end_date = self.get_date_range(period)

        bookings = self.get_completed_bookings_queryset(start_date, end_date)

        # Calculate revenue per service
        service_revenue = (
            bookings.values(
                "services__uid", "services__name", "services__category__name"
            )
            .annotate(
                total_revenue=Sum(
                    F("services__price")
                    * (1 - F("services__discount_percentage") / 100),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                ),
                booking_count=Count("id"),
            )
            .filter(total_revenue__gt=0)
            .order_by("-total_revenue")[:5]
        )

        # Format response for line chart
        data = []
        for item in service_revenue:
            data.append(
                {
                    "service_uid": item["services__uid"],
                    "service_name": item["services__name"],
                    "category_name": item["services__category__name"],
                    "revenue": float(item["total_revenue"] or Decimal("0.00")),
                    "booking_count": item["booking_count"],
                }
            )

        return Response(
            {
                "period": period,
                "start_date": start_date,
                "end_date": end_date,
                "data": data,
            }
        )


class TopProductsRevenueView(BaseRevenueAnalyticsView):
    """
    GET /api/analytics/revenue/products/?period=last_year
    Returns top 5 individual products by revenue (Line chart data)
    """

    def get(self, request, *args, **kwargs):
        period = request.query_params.get("period", "this_month")
        start_date, end_date = self.get_date_range(period)

        bookings = self.get_completed_bookings_queryset(start_date, end_date)

        # Calculate revenue per product
        product_revenue = (
            bookings.values(
                "products__uid", "products__name", "products__category__name"
            )
            .annotate(
                total_revenue=Sum(
                    "products__price",
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                ),
                booking_count=Count("id"),
            )
            .filter(total_revenue__gt=0)
            .order_by("-total_revenue")[:5]
        )

        # Format response for line chart
        data = []
        for item in product_revenue:
            data.append(
                {
                    "product_uid": item["products__uid"],
                    "product_name": item["products__name"],
                    "category_name": item["products__category__name"],
                    "revenue": float(item["total_revenue"] or Decimal("0.00")),
                    "booking_count": item["booking_count"],
                }
            )

        return Response(
            {
                "period": period,
                "start_date": start_date,
                "end_date": end_date,
                "data": data,
            }
        )


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

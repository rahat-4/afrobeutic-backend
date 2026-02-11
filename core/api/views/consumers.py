from django.http import FileResponse

from rest_framework import status
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveAPIView,
    RetrieveUpdateAPIView,
    get_object_or_404,
)
from rest_framework.views import APIView
from rest_framework.response import Response

from common.authentication import CustomerJWTAuthentication

from apps.salon.models import Booking, Customer, Salon
from apps.salon.choices import BookingStatus, CustomerType

from common.filters import BookingDateFilter
from common.utils import generate_receipt_pdf

from ..serializers.consumers import CustomerProfileSerializer, CustomerBookingSerializer


class CustomerProfileView(RetrieveUpdateAPIView):
    queryset = Customer.objects.filter(type=CustomerType.CUSTOMER)
    serializer_class = CustomerProfileSerializer
    authentication_classes = [CustomerJWTAuthentication]
    permission_classes = []

    def get_object(self):
        return self.request.customer


class CustomerBookingListView(ListCreateAPIView):
    serializer_class = CustomerBookingSerializer
    authentication_classes = [CustomerJWTAuthentication]
    permission_classes = []
    filterset_class = BookingDateFilter
    search_fields = ["booking_id"]

    ordering_fields = ["created_at", "booking_date", "booking_time"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return self.request.customer.customer_bookings.all()

    def perform_create(self, serializer):
        serializer.save(customer=self.request.customer)


class CustomerBookingDetailView(RetrieveUpdateAPIView):
    queryset = Booking.objects.all()
    serializer_class = CustomerBookingSerializer
    authentication_classes = [CustomerJWTAuthentication]
    permission_classes = []
    lookup_field = "uid"
    lookup_url_kwarg = "booking_uid"


class CustomerReceiptDownloadAPIView(APIView):
    authentication_classes = [CustomerJWTAuthentication]
    permission_classes = []

    def get(self, request, booking_uid, *args, **kwargs):
        try:
            booking = Booking.objects.get(uid=booking_uid, customer=request.customer)
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

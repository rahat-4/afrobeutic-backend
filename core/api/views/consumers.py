from django.http import FileResponse

from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveAPIView, RetrieveUpdateAPIView
from rest_framework.views import APIView
from rest_framework.response import Response

from common.authentication import CustomerJWTAuthentication

from apps.salon.models import Booking, Customer
from apps.salon.choices import BookingStatus, CustomerType

from common.utils import generate_receipt_pdf

from ..serializers.consumers import CustomerProfileSerializer, CustomerBookingSerializer


class CustomerProfileView(RetrieveUpdateAPIView):
    queryset = Customer.objects.filter(type=CustomerType.CUSTOMER)
    serializer_class = CustomerProfileSerializer
    authentication_classes = [CustomerJWTAuthentication]

    def get_object(self):
        return self.request.customer


class CustomerBookingListView(ListAPIView):
    serializer_class = CustomerBookingSerializer
    authentication_classes = [CustomerJWTAuthentication]

    def get_queryset(self):
        return self.request.customer.bookings.all()


class CustomerBookingDetailView(RetrieveAPIView):
    queryset = Booking.objects.all()
    serializer_class = CustomerBookingSerializer
    authentication_classes = [CustomerJWTAuthentication]
    lookup_field = "uid"
    lookup_url_kwarg = "booking_uid"


class CustomerReceiptDownloadAPIView(APIView):
    authentication_classes = [CustomerJWTAuthentication]

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

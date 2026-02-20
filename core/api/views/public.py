from django.db import transaction

from rest_framework.generics import (
    ListAPIView,
    CreateAPIView,
    RetrieveAPIView,
    RetrieveUpdateAPIView,
)

from apps.salon.models import Booking, Salon
from apps.salon.choices import SalonStatus

from common.filters import SalonAvailabilityFilter
from common.locations import get_customer_ip_address, get_country_from_ip

from ..serializers.public import PublicSalonSerializer, PublicSalonBookingSerializer


class PublicSalonListView(ListAPIView):
    serializer_class = PublicSalonSerializer
    permission_classes = []
    filterset_class = SalonAvailabilityFilter
    search_fields = ["name"]

    def get_queryset(self):
        with transaction.atomic():
            ip = get_customer_ip_address(self.request)
            country_code = get_country_from_ip(ip)
            queryset = Salon.objects.filter(
                status=SalonStatus.ACTIVE, country=country_code
            )
            return queryset


class PublicSalonDetailView(RetrieveAPIView):
    queryset = Salon.objects.filter(status=SalonStatus.ACTIVE)
    serializer_class = PublicSalonSerializer
    permission_classes = []
    lookup_field = "uid"
    lookup_url_kwarg = "salon_uid"


class PublicSalonBookingView(CreateAPIView):
    queryset = Booking.objects.all()
    serializer_class = PublicSalonBookingSerializer
    permission_classes = []

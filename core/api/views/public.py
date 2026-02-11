from rest_framework.generics import (
    ListAPIView,
    CreateAPIView,
    RetrieveAPIView,
    RetrieveUpdateAPIView,
)

from apps.salon.models import Booking, Salon
from apps.salon.choices import SalonStatus

from common.filters import SalonAvailabilityFilter

from ..serializers.public import PublicSalonSerializer, PublicSalonBookingSerializer


class PublicSalonListView(ListAPIView):
    queryset = Salon.objects.filter(status=SalonStatus.ACTIVE)
    serializer_class = PublicSalonSerializer
    permission_classes = []
    filterset_class = SalonAvailabilityFilter
    search_fields = ["name"]


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

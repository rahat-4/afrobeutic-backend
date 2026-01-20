from rest_framework.generics import ListCreateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated

from apps.salon.models import Booking

from ..serializers.public import PublicBookingSerializer

class PublicBookingListView(ListCreateAPIView):

    def get_permissions(self):
        if self.request.method == "GET":
            self.permission_classes = [IsAuthenticated]
        else:
            self.permission_classes = [AllowAny]

        return super().get_permissions()

    def get_serializer_class(self):
        return PublicBookingSerializer
    
    def get_queryset(self):
        return Booking.objects.filter()
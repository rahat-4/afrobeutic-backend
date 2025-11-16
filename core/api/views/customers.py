from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from rest_framework.generics import ListAPIView, RetrieveAPIView, get_object_or_404

from apps.salon.choices import CustomerType
from apps.salon.models import Customer

from common.permissions import IsOwnerOrAdminOrStaff

from ..serializers.customers import CustomerSerializer


class CustomerListView(ListAPIView):
    serializer_class = CustomerSerializer
    permission_classes = [IsOwnerOrAdminOrStaff]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["first_name", "last_name", "email", "phone", "salon__name"]
    filterset_fields = {
        "created_at": ["gte", "lte"],
        "updated_at": ["gte", "lte"],
        "salon__uid": ["exact"],
    }
    ordering_fields = ["first_name", "last_name", "created_at", "updated_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        account = self.request.account
        return Customer.objects.filter(account=account, type=CustomerType.CUSTOMER)


class CustomerDetailView(RetrieveAPIView):
    serializer_class = CustomerSerializer
    permission_classes = [IsOwnerOrAdminOrStaff]
    lookup_field = "uid"
    lookup_url_kwarg = "customer_uid"

    def get_object(self):
        account = self.request.account
        customer_uid = self.kwargs["customer_uid"]
        return get_object_or_404(Customer, account=account, uid=customer_uid)

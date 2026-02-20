from rest_framework.generics import ListAPIView, get_object_or_404
from rest_framework.exceptions import ValidationError

from apps.salon.models import (
    Employee,
    Salon,
    Service,
    Product,
    ServiceCategory,
    ServiceSubCategory,
)

from ..serializers.filters import (
    FilterEmployeeSerializer,
    FilterServiceSerializer,
    FilterProductSerializer,
    FilterServiceCategorySerializer,
    FilterServiceSubCategorySerializer,
)


class FilterEmployeeListView(ListAPIView):
    serializer_class = FilterEmployeeSerializer  # Assuming a similar serializer exists
    pagination_class = None

    def get_queryset(self):
        account = self.request.account

        salon_uid = self.kwargs.get("salon_uid")
        salon = get_object_or_404(Salon, uid=salon_uid, account=account)

        queryset = Employee.objects.filter(salon=salon, account=account)

        return queryset


class FilterServiceListView(ListAPIView):
    serializer_class = FilterServiceSerializer
    pagination_class = None
    permission_classes = []

    def get_queryset(self):
        salon_uid = self.kwargs.get("salon_uid")
        salon = get_object_or_404(Salon, uid=salon_uid)

        queryset = Service.objects.filter(salon=salon)

        return queryset


class FilterProductListView(ListAPIView):
    serializer_class = FilterProductSerializer
    pagination_class = None
    permission_classes = []

    def get_queryset(self):
        salon_uid = self.kwargs.get("salon_uid")
        salon = get_object_or_404(Salon, uid=salon_uid)

        queryset = Product.objects.filter(salon=salon)

        return queryset


class FilterServiceCategoryListView(ListAPIView):
    queryset = ServiceCategory.objects.all()
    serializer_class = FilterServiceCategorySerializer
    pagination_class = None
    permission_classes = []


class FilterServiceSubCategoryListView(ListAPIView):
    queryset = ServiceSubCategory.objects.all()
    serializer_class = FilterServiceSubCategorySerializer
    pagination_class = None
    permission_classes = []
    filterset_fields = ["category__name"]

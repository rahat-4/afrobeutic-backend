from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import filters
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView, ListCreateAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.salon.models import (
    Customer,
    ServiceCategory,
    ServiceSubCategory,
    ProductCategory,
    ProductSubCategory,
)

from .models import Category
from .serializers import (
    LeadCustomerSerializer,
    ServiceCategorySerializer,
    ServiceSubCategorySerializer,
    ProductCategorySerializer,
    ProductSubCategorySerializer,
)


class CategoryListView(ListAPIView):
    queryset = Category.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["category_type"]
    pagination_class = None

    def get_queryset(self):
        account = self.request.account

        # Ensure 'category_type' is provided
        category_type = self.request.query_params.get("category_type")
        if not category_type:
            raise ValidationError(
                {"category_type": "This query parameter is required."}
            )

        return self.queryset.filter(account=account, category_type=category_type)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        names = queryset.values_list("name", flat=True)
        return Response(list(names))


class LeadCustomerListView(ListAPIView):
    queryset = Customer.objects.all()
    serializer_class = LeadCustomerSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ["phone"]


class ServiceCategoryListView(ListAPIView):
    queryset = ServiceCategory.objects.all().order_by("created_at")
    serializer_class = ServiceCategorySerializer
    permission_classes = [IsAuthenticated]


class ServiceSubCategoryListView(ListCreateAPIView):
    serializer_class = ServiceSubCategorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        service_category_uid = self.kwargs.get("service_category_uid")
        return ServiceSubCategory.objects.filter(
            category__uid=service_category_uid
        ).order_by("created_at")

    def perform_create(self, serializer):
        service_category_uid = self.kwargs.get("service_category_uid")

        try:
            service_category = ServiceCategory.objects.get(uid=service_category_uid)
        except ServiceCategory.DoesNotExist:
            raise ValidationError("Invalid service category.")

        if service_category.name.upper() != "OTHER_SERVICES":
            raise ValidationError(
                {
                    "category": (
                        "Custom sub-categories can only be created under "
                        "the 'Other Services' service category."
                    )
                }
            )

        serializer.save(category=service_category, is_custom=True)


class ProductCategoryListView(ListAPIView):
    queryset = ProductCategory.objects.all().order_by("created_at")
    serializer_class = ProductCategorySerializer
    permission_classes = [IsAuthenticated]


class ProductSubCategoryListView(ListCreateAPIView):
    serializer_class = ProductSubCategorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        product_category_uid = self.kwargs.get("product_category_uid")
        return ProductSubCategory.objects.filter(
            category__uid=product_category_uid
        ).order_by("created_at")

    def perform_create(self, serializer):
        product_category_uid = self.kwargs.get("product_category_uid")

        try:
            product_category = ProductCategory.objects.get(uid=product_category_uid)
        except ProductCategory.DoesNotExist:
            raise ValidationError("Invalid product category.")

        if product_category.name.upper() != "OTHER_PRODUCTS":
            raise ValidationError(
                {
                    "category": (
                        "Custom sub-categories can only be created under "
                        "the 'Other Products' product category."
                    )
                }
            )

        serializer.save(category=product_category, is_custom=True)

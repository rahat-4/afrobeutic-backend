from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import filters
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.salon.models import Customer

from .models import Category
from .serializers import LeadCustomerSerializer


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

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework.generics import ListAPIView
from rest_framework.response import Response

from .models import Category


class CategoryListView(ListAPIView):
    queryset = Category.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["category_type"]
    pagination_class = None

    def get_queryset(self):
        account = self.request.account
        return self.queryset.filter(account=account)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        names = queryset.values_list("name", flat=True)
        return Response(list(names))

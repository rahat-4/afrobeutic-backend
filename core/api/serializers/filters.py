from rest_framework import serializers

from apps.salon.models import (
    Employee,
    Service,
    Product,
    ServiceCategory,
    ServiceSubCategory,
)


class FilterEmployeeSerializer(serializers.ModelSerializer):
    designation = serializers.CharField(source="designation.name")

    class Meta:
        model = Employee
        fields = ["uid", "image", "name", "designation"]


class FilterServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ["uid", "name"]


class FilterProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["uid", "name"]


class FilterServiceCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCategory
        fields = ["uid", "name"]


class FilterServiceSubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceSubCategory
        fields = ["uid", "name"]

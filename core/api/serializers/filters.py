from rest_framework import serializers

from apps.salon.models import Employee, Service, Product


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

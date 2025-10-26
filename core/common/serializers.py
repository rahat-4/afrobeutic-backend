from django.contrib.auth import get_user_model

from rest_framework import serializers

from apps.salon.models import Customer, Employee

User = get_user_model()


class UserSlimSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["uid", "first_name", "last_name", "email", "gender"]


class CustomerSlimSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["uid", "name", "phone"]


class EmployeeSlimSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ["uid", "employee_id", "name", "phone", "designation", "image"]

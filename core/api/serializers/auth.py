from django.contrib.auth import get_user_model

from rest_framework import serializers


User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = [
            "uid",
            "first_name",
            "last_name",
            "email",
            "country",
            "password",
            "confirm_password",
        ]

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists.")
        return value

    def validate(self, attrs):
        if attrs.get("password") != attrs.get("confirm_password"):
            raise serializers.ValidationError("Passwords do not match.")
        return attrs

    def create(self, validated_data):
        validated_data.pop("confirm_password", None)
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.is_active = False  # User must verify email to activate account
        user.set_password(password)
        user.save()
        return user

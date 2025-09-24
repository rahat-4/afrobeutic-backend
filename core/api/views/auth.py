from django.utils.http import urlsafe_base64_decode
from django.contrib.auth import get_user_model

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.authentication.emails import send_verification_email

from common.utils import email_token_generator

from ..serializers.auth import UserRegistrationSerializer

User = get_user_model()


class UserRegistrationView(APIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = []

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Send verification email
        send_verification_email(user)

        return Response(
            {"message": "Verification email sent.", "expires_in_minutes": 60},
            status=status.HTTP_201_CREATED,
        )


class VerifyEmailView(APIView):
    permission_classes = []

    def get(self, request, uid64, token):
        try:
            uid = urlsafe_base64_decode(uid64).decode()
            user = User.objects.get(uid=uid)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            return Response(
                {"message": "Invalid verification link."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user.is_active:
            return Response(
                {"message": "Account already verified."},
                status=status.HTTP_200_OK,
            )

        if email_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            return Response(
                {"message": "Email verified successfully."},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"message": "Verification link expired or invalid."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ResendVerificationEmailView(APIView):
    permission_classes = []

    def post(self, request):
        email = request.data.get("email")

        if not email:
            return Response(
                {"error": "Email is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if user.is_active:
            return Response(
                {"message": "Account already verified."},
                status=status.HTTP_200_OK,
            )

        # Resend verification email
        success = send_verification_email(user)
        if success:
            return Response(
                {"message": "Verification email resent.", "expires_in_minutes": 60},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"error": "Failed to send email."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

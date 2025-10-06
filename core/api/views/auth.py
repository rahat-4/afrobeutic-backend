from datetime import timezone
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.authentication.models import AccountInvitation
from apps.authentication.emails import (
    send_verification_email,
    send_account_invitation_email,
)

from common.permissions import IsOwnerOrAdmin
from common.utils import email_token_generator

from ..serializers.auth import UserRegistrationSerializer, AccountInvitationSerializer

User = get_user_model()


class UserRegistrationView(APIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = []
    throttle_scope = "register"

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


class AccountInvitationView(APIView):
    serializer_class = AccountInvitationSerializer
    permission_classes = [IsOwnerOrAdmin]
    throttle_scope = "invite"

    def post(self, request):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        invitation = serializer.save(
            invited_by=request.user,
            expires_at=timezone.now() + timedelta(minutes=60),
        )

        # Send invitation email
        send_account_invitation_email(invitation)

        return Response(
            {"message": "Account invitation sent.", "expires_in_minutes": 60},
            status=status.HTTP_200_OK,
        )


class AcceptInvitationView(APIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = []

    def get(self, request, token):
        """Handle existing user invitation acceptance"""
        try:
            invitation = AccountInvitation.objects.get(uid=token, is_accepted=False)
        except AccountInvitation.DoesNotExist:
            return Response(
                {"message": "Invalid invitation link."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if invitation.is_expired():
            return Response(
                {"message": "Invitation link has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        email = invitation.email.lower()
        existing_user = User.objects.filter(email__iexact=email).first()

        if existing_user:
            # ✅ Existing user: update role, activate, mark invitation accepted
            existing_user.role = invitation.role
            existing_user.is_active = True
            existing_user.save()

            invitation.is_accepted = True
            invitation.save()

            return Response(
                {"message": "Invitation accepted. You can now log in."},
                status=status.HTTP_200_OK,
            )
        else:
            # New user needs to register via POST
            return Response(
                {
                    "message": "Please complete registration.",
                    "email": email,
                    "role": invitation.role,
                    "requires_registration": True,
                },
                status=status.HTTP_200_OK,
            )

    def post(self, request, token):
        """Handle new user registration"""
        try:
            invitation = AccountInvitation.objects.get(uid=token, is_accepted=False)
        except AccountInvitation.DoesNotExist:
            return Response(
                {"message": "Invalid invitation link."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if invitation.is_expired():
            return Response(
                {"message": "Invitation link has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        email = invitation.email.lower()
        existing_user = User.objects.filter(email__iexact=email).first()

        if existing_user:
            return Response(
                {
                    "message": "User already exists. Please use GET to accept invitation."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ✅ New user: validate and register using serializer
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        if user.email.lower() != email:
            # Email doesn't match invitation — delete user and return error
            user.delete()
            return Response(
                {"message": "Email mismatch. Please use the invited email address."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Complete invitation
        invitation.is_accepted = True
        invitation.save()

        # Set role and send email verification
        user.role = invitation.role
        user.save()

        send_verification_email(user)

        return Response(
            {"message": "Account created. Verification email sent."},
            status=status.HTTP_201_CREATED,
        )

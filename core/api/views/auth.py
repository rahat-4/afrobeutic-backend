from urllib.parse import urlencode

from datetime import timezone
from django.utils.http import urlsafe_base64_decode
from django.http import HttpResponseRedirect
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from rest_framework_simplejwt.views import TokenObtainPairView

from apps.authentication.choices import AccountMembershipRole
from apps.authentication.models import AccountInvitation, AccountMembership
from apps.authentication.emails import (
    send_verification_email,
    send_account_invitation_email,
)

from common.permissions import IsOwnerOrAdmin
from common.throttles import RoleBasedLoginThrottle
from common.utils import email_token_generator

from ..serializers.auth import (
    UserRegistrationSerializer,
    CustomTokenObtainPairSerializer,
    MeSerializer,
)

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
            params = urlencode({"error": "invalid_link"})
            return HttpResponseRedirect(
                f"http://localhost:3000/auth/signup/error?{params}"
            )

        if user.is_active:
            return HttpResponseRedirect("http://localhost:3000/auth/login")

        if email_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            return HttpResponseRedirect("http://localhost:3000/auth/login")
        else:
            params = urlencode({"error": "expired_or_invalid"})
            return HttpResponseRedirect(
                f"http://localhost:3000/auth/signup/error?{params}"
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


class AcceptInvitationView(APIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = []

    def get(self, request, token):
        try:
            invitation = AccountInvitation.objects.get(uid=token, is_accepted=False)
        except AccountInvitation.DoesNotExist:
            params = urlencode({"error": "invalid_invitation"})
            return HttpResponseRedirect(
                f"http://localhost:3000/auth/signup/error?{params}"
            )

        if invitation.is_expired():
            params = urlencode({"error": "expired_invitation"})
            return HttpResponseRedirect(
                f"http://localhost:3000/auth/signup/error?{params}"
            )

        email = invitation.email.lower()
        existing_user = User.objects.filter(email__iexact=email).first()

        if existing_user:
            # ✅ Auto-accept and activate
            AccountMembership.objects.get_or_create(
                user=existing_user,
                account=invitation.account,
                defaults={"role": invitation.role},
            )
            existing_user.is_active = True
            existing_user.save()

            invitation.is_accepted = True
            invitation.accepted_at = timezone.now()
            invitation.save()

            # ✅ Redirect to login
            return HttpResponseRedirect("http://localhost:3000/auth/login")
        else:
            # 🚪 Redirect to register page with email + token
            params = urlencode(
                {"email": email, "role": invitation.role, "token": invitation.uid}
            )
            return HttpResponseRedirect(f"http://localhost:3000/auth/signup?{params}")

    def post(self, request, token):
        try:
            invitation = AccountInvitation.objects.get(uid=token, is_accepted=False)
        except AccountInvitation.DoesNotExist:
            params = urlencode({"error": "invalid_invitation"})
            return HttpResponseRedirect(
                f"http://localhost:3000/auth/signup/error?{params}"
            )

        if invitation.is_expired():
            params = urlencode({"error": "expired_invitation"})
            return HttpResponseRedirect(
                f"http://localhost:3000/auth/signup/error?{params}"
            )

        email = invitation.email.lower()
        existing_user = User.objects.filter(email__iexact=email).first()

        if existing_user:
            params = urlencode({"error": "already_exists"})
            return HttpResponseRedirect(f"http://localhost:3000/login?{params}")

        # Validate new user data
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        if user.email.lower() != email:
            user.delete()
            params = urlencode({"error": "email_mismatch"})
            return HttpResponseRedirect(
                f"http://localhost:3000/register-invite?{params}"
            )

        # Complete invitation
        invitation.is_accepted = True
        invitation.save()

        AccountMembership.objects.create(
            user=user,
            account=invitation.account,
            role=invitation.role,
        )

        # Send verification email
        send_verification_email(user)

        # ✅ Redirect to email verification info page
        return HttpResponseRedirect(f"http://localhost:3000/verify-email?email={email}")


class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = [RoleBasedLoginThrottle]


class MeView(APIView):
    def get(self, request, *args, **kwargs):
        serializer = MeSerializer(request.user, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, *args, **kwargs):
        serializer = MeSerializer(
            request.user, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

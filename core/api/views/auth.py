from urllib.parse import urlencode

from datetime import timezone
from django.utils.http import urlsafe_base64_decode
from django.http import HttpResponseRedirect
from django.contrib.auth import get_user_model
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken


from apps.authentication.models import AccountInvitation, AccountMembership
from apps.authentication.emails import (
    send_verification_email,
)

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
                f"https://www.afrobeutic.com/auth/signup/error?{params}"
            )

        if user.is_active:
            return HttpResponseRedirect(
                "https://www.afrobeutic.com/auth/signup/already-verified"
            )

        if email_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            return HttpResponseRedirect("https://www.afrobeutic.com/auth/login")
        else:
            params = urlencode({"error": "expired_or_invalid"})
            return HttpResponseRedirect(
                f"https://www.afrobeutic.com/auth/signup/error?{params}"
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
                f"https://www.afrobeutic.com/auth/signup/error?{params}"
            )

        if invitation.is_expired():
            params = urlencode({"error": "expired_invitation"})
            return HttpResponseRedirect(
                f"https://www.afrobeutic.com/auth/signup/error?{params}"
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
            return HttpResponseRedirect("https://www.afrobeutic.com/auth/login")
        else:
            # 🚪 Redirect to register page with email + token
            params = urlencode(
                {"email": email, "role": invitation.role, "token": invitation.uid}
            )
            return HttpResponseRedirect(
                f"https://www.afrobeutic.com/auth/accept-invitation?{params}"
            )

    def post(self, request, token):
        try:
            invitation = AccountInvitation.objects.get(uid=token, is_accepted=False)
        except AccountInvitation.DoesNotExist:
            params = urlencode({"error": "invalid_invitation"})
            return HttpResponseRedirect(
                f"https://www.afrobeutic.com/auth/signup/error?{params}"
            )

        if invitation.is_expired():
            params = urlencode({"error": "expired_invitation"})
            return HttpResponseRedirect(
                f"https://www.afrobeutic.com/auth/signup/error?{params}"
            )

        email = invitation.email.lower()
        existing_user = User.objects.filter(email__iexact=email).first()

        if existing_user:
            params = urlencode({"error": "already_exists"})
            return HttpResponseRedirect(f"https://www.afrobeutic.com/login?{params}")

        # Validate new user data
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        if user.email.lower() != email:
            user.delete()
            params = urlencode({"error": "email_mismatch"})
            return HttpResponseRedirect(
                f"https://www.afrobeutic.com/register-invite?{params}"
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
        return HttpResponseRedirect(
            f"https://www.afrobeutic.com/verify-email?email={email}"
        )


class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = [RoleBasedLoginThrottle]


class LogoutView(APIView):
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh_token")
            if not refresh_token:
                return Response(
                    {"error": "Refresh token is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(
                {"message": "Successfully logged out"},
                status=status.HTTP_205_RESET_CONTENT,
            )
        except Exception as e:
            return Response(
                {"error": "Invalid token or token already blacklisted"},
                status=status.HTTP_400_BAD_REQUEST,
            )


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


# # utils.py
# def set_jwt_cookies(response, access, refresh):
#     # ACCESS TOKEN COOKIE
#     response.set_cookie(
#         "access",
#         access,
#         httponly=True,      # JavaScript cannot read
#         secure=True,        # HTTPS only
#         samesite="None",    # required for cross-site cookies
#         max_age=300,        # 5 minutes
#     )

#     # REFRESH TOKEN COOKIE
#     response.set_cookie(
#         "refresh",
#         refresh,
#         httponly=True,
#         secure=True,
#         samesite="None",
#         max_age=7 * 24 * 3600,  # 7 days
#     )

#     return response


# from rest_framework.response import Response
# from rest_framework import status
# from rest_framework.views import APIView
# from rest_framework.permissions import IsAuthenticated
# from rest_framework_simplejwt.tokens import RefreshToken
# from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
# from django.contrib.auth import authenticate
# from .utils import set_jwt_cookies


# # ----------------------------
# # LOGIN
# # ----------------------------
# class LoginView(APIView):
#     def post(self, request):
#         username = request.data.get("username")
#         password = request.data.get("password")

#         user = authenticate(username=username, password=password)
#         if not user:
#             return Response({"detail": "Invalid credentials"}, status=400)

#         refresh = RefreshToken.for_user(user)
#         access = str(refresh.access_token)

#         response = Response({"detail": "Logged in"}, status=200)
#         return set_jwt_cookies(response, access, str(refresh))


# # ----------------------------
# # REFRESH TOKEN
# # ----------------------------
# class RefreshView(APIView):
#     def post(self, request):
#         refresh_token = request.COOKIES.get("refresh")

#         if not refresh_token:
#             return Response({"detail": "No refresh token"}, status=401)

#         try:
#             refresh = RefreshToken(refresh_token)
#             access = refresh.access_token
#         except TokenError:
#             return Response({"detail": "Token expired or invalid"}, status=401)

#         # ROTATE REFRESH TOKEN
#         refresh.blacklist()
#         new_refresh = RefreshToken.for_user(refresh.user)

#         response = Response({"detail": "Token refreshed"}, status=200)
#         return set_jwt_cookies(response, str(access), str(new_refresh))


# # ----------------------------
# # LOGOUT
# # ----------------------------
# class LogoutView(APIView):
#     def post(self, request):
#         response = Response({"detail": "Logged out"}, status=200)
#         response.delete_cookie("access")
#         response.delete_cookie("refresh")
#         return response

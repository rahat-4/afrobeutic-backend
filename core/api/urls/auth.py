from django.urls import path

from ..views.auth import (
    AcceptInvitationView,
    UserRegistrationView,
    ResendVerificationEmailView,
    VerifyEmailView,
    LoginView,
    LogoutView,
    MeView,
    SendCustomerOTPView,
    VerifyCustomerOTPView,
)

urlpatterns = [
    path(
        "/verify-otp",
        VerifyCustomerOTPView.as_view(),
        name="auth.verify-customer-otp",
    ),
    path(
        "/send-otp",
        SendCustomerOTPView.as_view(),
        name="auth.send-customer-otp",
    ),
    path(
        "/accept-invitation/<token>/",
        AcceptInvitationView.as_view(),
        name="auth.accept-invitation",
    ),
    path("/me", MeView.as_view(), name="auth.me"),
    path("/login", LoginView.as_view(), name="auth.login"),
    path("/logout", LogoutView.as_view(), name="auth.logout"),
    path(
        "/resend-verification-email",
        ResendVerificationEmailView.as_view(),
        name="auth.resend-verification-email",
    ),
    path(
        "/verify-email/<uid64>/<token>/",
        VerifyEmailView.as_view(),
        name="auth.verify-email",
    ),
    path("/register", UserRegistrationView.as_view(), name="auth.register"),
]

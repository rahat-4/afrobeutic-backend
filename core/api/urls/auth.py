from django.urls import path

from ..views.auth import (
    UserRegistrationView,
    ResendVerificationEmailView,
    VerifyEmailView,
    AccountInvitationView,
    AcceptInvitationView,
    LoginView,
)

urlpatterns = [
    path("/login", LoginView.as_view(), name="auth.login"),
    path(
        "/accept-invite/<token>/",
        AcceptInvitationView.as_view(),
        name="auth.accept-invite",
    ),
    path(
        "/account-invite",
        AccountInvitationView.as_view(),
        name="auth.invite",
    ),
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

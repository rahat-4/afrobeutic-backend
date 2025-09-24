from django.urls import path

from ..views.auth import (
    UserRegistrationView,
    ResendVerificationEmailView,
    VerifyEmailView,
)

urlpatterns = [
    path(
        "/verify-email/<uid64>/<token>/",
        VerifyEmailView.as_view(),
        name="auth.verify-email",
    ),
    path(
        "/resend-verification-email",
        ResendVerificationEmailView.as_view(),
        name="auth.resend-verification-email",
    ),
    path("/register", UserRegistrationView.as_view(), name="auth.register"),
]

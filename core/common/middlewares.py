import re
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse

from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.authentication.models import Account


class CurrentAccountMiddleware(MiddlewareMixin):
    EXCLUDED_PATHS = [
        # Admin paths
        re.compile(r"^/api/admin/.*$"),
        # Public paths
        re.compile(r"^/admin/.*$"),
        re.compile(r"^/api/auth/register/?$"),
        re.compile(r"^/api/auth/login/?$"),
        re.compile(r"^/api/auth/logout/?$"),
        re.compile(r"^/api/auth/verify-email/.*$"),
        re.compile(r"^/api/auth/resend-verification-email/?$"),
        re.compile(r"^/api/auth/accept-invitation/[0-9a-fA-F-]+/?$"),
        # API documentation and schema
        re.compile(r"^/api/docs/?$"),
        re.compile(r"^/api/redoc/?$"),
        re.compile(r"^/api/schema/?$"),
        # JWT Token endpoints
        re.compile(r"^/api/token/?$"),
        re.compile(r"^/api/token/refresh/?$"),
        re.compile(r"^/api/token/verify/?$"),
        # Media and static files
        re.compile(r"^/media/.*$"),
        re.compile(r"^/static/.*$"),
        # Stripe webhook
        re.compile(r"^/api/webhook/stripe/?$"),
    ]

    def is_excluded_path(self, path):
        test = any(pattern.match(path) for pattern in self.EXCLUDED_PATHS)
        print("is_excluded_path", path, test)
        return test

    def process_request(self, request):
        jwt_auth = JWTAuthentication()
        try:
            user_auth_tuple = jwt_auth.authenticate(request)
            if user_auth_tuple is not None:
                request.user, _ = user_auth_tuple
        except Exception:
            pass

        if request.path == "/api/auth/me":
            if getattr(request.user, "is_staff", False):
                request.account = None
                return

        if self.is_excluded_path(request.path):
            request.account = None
            return

        account_id = request.headers.get("X-Account-Id")
        if account_id:
            try:
                account = Account.objects.get(uid=account_id)
                request.account = account
            except Account.DoesNotExist:
                return JsonResponse({"error": "Invalid account ID"}, status=400)
        else:
            return JsonResponse({"error": "Missing X-ACCOUNT-ID header"}, status=400)

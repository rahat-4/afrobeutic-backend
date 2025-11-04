import re
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse

from apps.authentication.models import Account


class CurrentAccountMiddleware(MiddlewareMixin):
    EXCLUDED_PATHS = [
        # Admin paths
        re.compile(r"^/api/admins/.*$"),
        # Public paths
        re.compile(r"^/admin/.*$"),
        re.compile(r"^/api/auth/register/?$"),
        re.compile(r"^/api/auth/login/?$"),
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
    ]

    def is_excluded_path(self, path):
        test = any(pattern.match(path) for pattern in self.EXCLUDED_PATHS)
        print("is_excluded_path", path, test)  # Debugging line
        return test

    def process_request(self, request):
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

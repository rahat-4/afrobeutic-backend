# middleware.py

from django.utils.deprecation import MiddlewareMixin
from apps.authentication.models import Account


class CurrentAccountMiddleware(MiddlewareMixin):
    def process_request(self, request):
        account_id = request.headers.get("X-Account-ID")
        if account_id:
            try:
                # Optional: check user has access to this account
                account = Account.objects.get(uid=account_id)
                request.account = account
            except Account.DoesNotExist:
                request.account = None
        else:
            request.account = None

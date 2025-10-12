from django.contrib.auth import get_user_model

from rest_framework.throttling import SimpleRateThrottle

from apps.authentication.models import AccountMembership
from apps.authentication.choices import AccountMembershipRole

User = get_user_model()


class RoleBasedLoginThrottle(SimpleRateThrottle):
    scope = "login"

    def get_cache_key(self, request, view):
        # Get the email from the request data
        email = request.data.get("email")
        if not email:
            return None  # no email provided, no throttling

        try:
            user = User.objects.get(email=email)
            membership = AccountMembership.objects.filter(user=user).first()
            if membership:
                if user.is_staff and membership.role in [
                    AccountMembershipRole.MANAGEMENT_ADMIN,
                    AccountMembershipRole.MANAGEMENT_STAFF,
                ]:
                    self.rate = "2/minute"
                else:
                    self.rate = "20/minute"
        except User.DoesNotExist:
            # If user not found, apply a default rate to prevent abuse
            self.rate = "20/minute"

        self.num_requests, self.duration = self.parse_rate(self.rate)

        # Use email as unique key (could also combine with IP)
        return self.cache_format % {"scope": self.scope, "ident": email.lower()}

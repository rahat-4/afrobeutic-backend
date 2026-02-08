import jwt

from django.conf import settings

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


class CustomerJWTAuthentication(BaseAuthentication):

    def authenticate(self, request):
        from apps.salon.models import Customer

        auth = request.headers.get("Authorization")

        if not auth or not auth.startswith("Bearer "):
            return None

        token = auth.split(" ")[1]

        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=["HS256"],
            )
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("Token expired")
        except jwt.InvalidTokenError:
            raise AuthenticationFailed("Invalid token")

        customer = Customer.objects.get(uid=payload["customer_uid"])
        request.customer = customer

        return (customer, None)

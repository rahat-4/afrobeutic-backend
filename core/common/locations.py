import os
from ipware import get_client_ip
from geoip2.database import Reader

from django.conf import settings

GEOIP_PATH = os.path.join(settings.BASE_DIR, "geoip/GeoLite2-Country.mmdb")


def get_customer_ip_address(request):
    """Get the client's IP address from the request."""
    ip, _ = get_client_ip(request)
    return ip


def get_country_from_ip(ip):
    """Get the country code from an IP address."""

    if not ip:
        return None

    try:
        reader = Reader(GEOIP_PATH)
        response = reader.country(ip)
        return response.country.iso_code
    except Exception:
        return None

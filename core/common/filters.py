from datetime import timedelta, datetime

from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from django_filters import rest_framework as filters
import django_filters
from django.utils import timezone
from django.utils.timezone import now
from django.contrib.auth import get_user_model

from apps.salon.models import Booking, Customer, Salon
from apps.support.models import AccountSupportTicket

User = get_user_model()


class AdminManagementRoleFilter(django_filters.FilterSet):
    role = django_filters.ChoiceFilter(
        choices=[
            ("MANAGEMENT_ADMIN", "MANAGEMENT_ADMIN"),
            ("MANAGEMENT_STAFF", "MANAGEMENT_STAFF"),
        ],
        method="filter_by_role",
    )

    class Meta:
        model = User
        fields = ["role", "country"]

    def filter_by_role(self, queryset, _name, value):
        if value == "MANAGEMENT_ADMIN":
            return queryset.filter(is_admin=True, is_staff=True)
        elif value == "MANAGEMENT_STAFF":
            return queryset.filter(is_admin=False, is_staff=True)
        return queryset


class SalonLeadFilter(django_filters.FilterSet):
    created_at = django_filters.DateFilter(field_name="created_at", lookup_expr="date")
    source = django_filters.CharFilter(field_name="source__name", lookup_expr="iexact")

    class Meta:
        model = Customer
        fields = {
            "created_at": [
                "gte",
                "lte",
            ],
        }


class CustomerEnquiryFilter(django_filters.FilterSet):
    source = django_filters.CharFilter(
        field_name="customer__source__name", lookup_expr="iexact"
    )

    class Meta:
        model = AccountSupportTicket
        fields = ["status", "type", "source"]


# ?date_type=today
# ?date_type=next_day
# ?date_type=previous_day
# ?date_type=this_month
# ?date_type=previous_month
# ?date_type=last_6_month
# ?date_type=one_year
# ?booking_date=2026-01-20
# ?start_date=2026-01-01&end_date=2026-01-31


class BookingDateFilter(filters.FilterSet):
    date_type = filters.CharFilter(method="filter_date_type")
    booking_date = filters.DateFilter()
    start_date = filters.DateFilter(method="filter_custom_range")
    end_date = filters.DateFilter(method="filter_custom_range")

    class Meta:
        model = Booking
        fields = ["status", "booking_date"]

    def filter_date_type(self, queryset, name, value):
        today = now().date()

        if value == "today":
            return queryset.filter(booking_date=today)

        if value == "next_day":
            return queryset.filter(booking_date=today + timedelta(days=1))

        if value == "previous_day":
            return queryset.filter(booking_date=today - timedelta(days=1))

        if value == "this_week":
            # Start from Monday of current week
            start_of_week = today - timedelta(days=today.weekday())
            return queryset.filter(
                booking_date__gte=start_of_week,
                booking_date__lte=today,
            )

        if value == "this_month":
            return queryset.filter(
                booking_date__year=today.year,
                booking_date__month=today.month,
            )

        if value == "previous_month":
            first_day_this_month = today.replace(day=1)
            last_day_prev_month = first_day_this_month - timedelta(days=1)

            return queryset.filter(
                booking_date__year=last_day_prev_month.year,
                booking_date__month=last_day_prev_month.month,
            )

        if value == "last_6_month":
            return queryset.filter(
                booking_date__gte=today - timedelta(days=180),
                booking_date__lte=today,
            )

        if value == "one_year":
            return queryset.filter(
                booking_date__gte=today - timedelta(days=365),
                booking_date__lte=today,
            )

        return queryset

    def filter_custom_range(self, queryset, name, value):
        start_date = self.data.get("start_date")
        end_date = self.data.get("end_date")

        if start_date and end_date:
            return queryset.filter(booking_date__range=[start_date, end_date])

        return queryset


# /salons/?latitude=23.8103&longitude=90.4125
# /salons/?latitude=23.8103&longitude=90.4125&radius_kilometer=10
# /salons/?latitude=23.8103&longitude=90.4125&date=2026-02-20&time=14:00
class SalonAvailabilityFilter(django_filters.FilterSet):
    city = django_filters.CharFilter(field_name="city", lookup_expr="iexact")
    category = django_filters.UUIDFilter(
        field_name="salon_services__category__uid", lookup_expr="exact"
    )
    sub_category = django_filters.UUIDFilter(
        field_name="salon_services__sub_category__uid", lookup_expr="exact"
    )
    latitude = django_filters.NumberFilter(method="filter_by_location")
    longitude = django_filters.NumberFilter(method="filter_by_location")
    radius_kilometer = django_filters.NumberFilter(method="filter_by_location")

    date = django_filters.DateFilter(method="date_filter")
    time = django_filters.TimeFilter(method="time_filter")

    class Meta:
        model = Salon
        fields = [
            "salon_category",
            "hair_service_types",
            "bridal_makeup_service_types",
            "salon_type",
            "additional_service_types",
            "city",
            "category",
            "sub_category",
            "latitude",
            "longitude",
            "radius_kilometer",
            "date",
            "time",
        ]

    @property
    def qs(self):
        parent = super().qs
        return parent.distinct()

    def filter_by_location(self, queryset, name, value):
        lat = self.data.get("latitude")
        lon = self.data.get("longitude")

        if not lat or not lon:
            return queryset

        radius = float(self.data.get("radius_kilometer", 3))
        radius = min(radius, 20)

        user_location = Point(float(lon), float(lat), srid=4326)

        queryset = (
            queryset.annotate(distance=Distance("location", user_location))
            .filter(location__distance_lte=(user_location, D(km=radius)))
            .order_by("distance")
        )

        return queryset

    def date_filter(self, queryset, name, value):
        if not value:
            return queryset

        day_name = value.strftime("%A").upper()

        return queryset.filter(
            opening_hours__day=day_name,
            opening_hours__is_closed=False,
        ).distinct()

    def time_filter(self, queryset, name, value):
        if not value:
            return queryset

        # If date exists → use that day's opening hours
        date_value = self.data.get("date")

        if not date_value:
            return queryset  # ignore time if no date

        if date_value:
            try:
                date_obj = datetime.strptime(date_value, "%Y-%m-%d")
                day_name = date_obj.strftime("%A").upper()

                queryset = queryset.filter(
                    opening_hours__day=day_name,
                    opening_hours__is_closed=False,
                )
            except ValueError:
                pass

        return queryset.filter(
            opening_hours__opening_time__lte=value,
            opening_hours__closing_time__gte=value,
        ).distinct()

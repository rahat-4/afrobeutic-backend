from zoneinfo import ZoneInfo
from datetime import timedelta, datetime

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


# ?available_now=true
# Show salons that are open RIGHT NOW (current day + current time)

# ?free_today=true
# Show salons that are open ANY TIME today (time does not matter)

# ?date=YYYY-MM-DD
# Show salons available on a specific date
# Example: ?date=2026-02-15

# ?date=YYYY-MM-DD&start_time=HH:MM&end_time=HH:MM
# Show salons available on a specific date AND within the given time range
# Example: ?date=2026-02-15&start_time=18:00&end_time=19:00

# ?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD
# Show salons available on ANY day within this date range
# Example: ?date_from=2026-02-15&date_to=2026-02-20

# ?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD&start_time=HH:MM&end_time=HH:MM
# Show salons available in the date range AND within the given time window
# Example: ?date_from=2026-02-15&date_to=2026-02-20&start_time=10:00&end_time=12:00

# ?city=Dhaka
# Filter salons by city

# ?country=Bangladesh
# Filter salons by country

# ?salon_type=men
# Filter salons by salon type

# ?salon_category=spa
# Filter salons by salon category

# ?search=salon_name
# Search salons by name


class SalonAvailabilityFilter(django_filters.FilterSet):
    city = django_filters.CharFilter(field_name="city", lookup_expr="iexact")
    available_now = django_filters.BooleanFilter(method="available_now_filter")
    free_today = django_filters.BooleanFilter(method="free_today_filter")

    date = django_filters.DateFilter(method="date_filter")
    start_time = django_filters.TimeFilter(method="ignore_filter")
    end_time = django_filters.TimeFilter(method="ignore_filter")

    date_from = django_filters.DateFilter(method="date_range_filter")
    date_to = django_filters.DateFilter(method="date_range_filter")

    class Meta:
        model = Salon
        fields = [
            "salon_category",
            "salon_type",
            "city",
            "country",
        ]

    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------
    def ignore_filter(self, queryset, name, value):
        return queryset

    def _get_local_now(self, salon):
        tz = ZoneInfo(salon.account.account_timezone)
        now = timezone.now().astimezone(tz)
        return now.replace(microsecond=0)

    def _filter_by_time_range(self, qs, start, end):
        if start and end:
            qs = qs.filter(
                opening_hours__opening_time__isnull=False,
                opening_hours__closing_time__isnull=False,
                opening_hours__opening_time__lte=start,
                opening_hours__closing_time__gte=end,
            )

        return qs

    # --------------------------------------------------
    # Filters
    # --------------------------------------------------

    def available_now_filter(self, queryset, name, value):
        if not value:
            return queryset

        salon_ids = []

        for salon in queryset.select_related("account"):
            now = self._get_local_now(salon)
            current_day = now.strftime("%A").upper()

            is_open = salon.opening_hours.filter(
                day=current_day,
                is_closed=False,
                opening_time__isnull=False,
                closing_time__isnull=False,
                opening_time__lte=now.time(),
                closing_time__gte=now.time(),
            ).exists()

            if is_open:
                salon_ids.append(salon.id)

        return queryset.filter(id__in=salon_ids)

    def free_today_filter(self, queryset, name, value):
        if not value:
            return queryset

        salon_ids = []

        for salon in queryset.select_related("account"):
            now = self._get_local_now(salon)
            today = now.strftime("%A").upper()

            is_open_today = salon.opening_hours.filter(
                day=today,
                is_closed=False,
            ).exists()

            if is_open_today:
                salon_ids.append(salon.id)

        return queryset.filter(id__in=salon_ids)

    def date_filter(self, queryset, name, value):
        if not value:
            return queryset

        day_name = value.strftime("%A").upper()

        qs = queryset.filter(
            opening_hours__day=day_name,
            opening_hours__is_closed=False,
        )

        start = self.form.cleaned_data.get("start_time")
        end = self.form.cleaned_data.get("end_time")

        qs = self._filter_by_time_range(qs, start, end)

        return qs.distinct()

    def date_range_filter(self, queryset, name, value):
        date_from = self.form.cleaned_data.get("date_from")
        date_to = self.form.cleaned_data.get("date_to")

        if not date_from or not date_to:
            return queryset

        weekdays = set()
        current = date_from

        while current <= date_to:
            weekdays.add(current.strftime("%A").upper())
            current += timedelta(days=1)

        qs = queryset.filter(
            opening_hours__day__in=weekdays,
            opening_hours__is_closed=False,
        )

        print(";;;;;;;;;;;;;;;;;;;;;;;;", qs)

        start = self.form.cleaned_data.get("start_time")
        end = self.form.cleaned_data.get("end_time")

        qs = self._filter_by_time_range(qs, start, end)

        return qs.distinct()

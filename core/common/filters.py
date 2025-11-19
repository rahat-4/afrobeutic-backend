import django_filters

from django.contrib.auth import get_user_model

from apps.salon.models import Customer
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

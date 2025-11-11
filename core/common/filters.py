import django_filters

from django.contrib.auth import get_user_model

from apps.salon.models import Lead

User = get_user_model()


class AdminManagementRoleFilter(django_filters.FilterSet):
    role = django_filters.ChoiceFilter(
        choices=[("ADMIN", "ADMIN"), ("STAFF", "STAFF")],
        method="filter_by_role",
    )

    class Meta:
        model = User
        fields = ["role", "country"]

    def filter_by_role(self, queryset, _name, value):
        if value == "ADMIN":
            return queryset.filter(is_admin=True, is_staff=True)
        elif value == "STAFF":
            return queryset.filter(is_admin=False, is_staff=True)
        return queryset


class SalonLeadFilter(django_filters.FilterSet):
    created_at = django_filters.DateFilter(field_name="created_at", lookup_expr="date")
    source = django_filters.CharFilter(field_name="source__name", lookup_expr="iexact")

    class Meta:
        model = Lead
        fields = {
            "created_at": [
                "gte",
                "lte",
            ],
        }

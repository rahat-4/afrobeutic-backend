import django_filters

from django.contrib.auth import get_user_model

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

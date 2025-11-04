from django.contrib.auth import get_user_model
from django.db.models import Prefetch

from rest_framework.generics import ListAPIView

from common.permissions import IsManagementAdminOrStaff
from apps.authentication.models import Account, AccountMembership

from ..serializers.admins import AdminUserSerializer, AdminAccountSerializer

User = get_user_model()


class AdminUserListView(ListAPIView):
    serializer_class = AdminUserSerializer
    permission_classes = [IsManagementAdminOrStaff]

    def get_queryset(self):
        # Create ordered memberships prefetch
        ordered_memberships = AccountMembership.objects.select_related(
            "account", "account__owner"
        ).ordered_by_role()

        return (
            User.objects.filter(is_staff=False)
            .order_by("created_at")
            .prefetch_related(Prefetch("memberships", queryset=ordered_memberships))
        )


class AdminAccountListView(ListAPIView):
    queryset = Account.objects.all().order_by("created_at")
    serializer_class = AdminAccountSerializer
    permission_classes = [IsManagementAdminOrStaff]

from rest_framework.permissions import BasePermission

from apps.authentication.models import AccountMembership
from apps.authentication.choices import AccountMembershipRole


def _has_account_membership(user, account, roles):
    if not (user and user.is_authenticated and account):
        return False
    return AccountMembership.objects.filter(
        user=user, account=account, role__in=roles
    ).exists()


class RolePermission(BasePermission):
    roles = ()

    def has_permission(self, request, view):
        return _has_account_membership(
            request.user, getattr(request, "account", None), self.roles
        )


class IsOwner(RolePermission):
    roles = (AccountMembershipRole.OWNER,)


class IsAdmin(RolePermission):
    roles = (AccountMembershipRole.ADMIN,)


class IsStaff(RolePermission):
    roles = (AccountMembershipRole.STAFF,)


class IsOwnerOrAdmin(RolePermission):
    roles = (AccountMembershipRole.OWNER, AccountMembershipRole.ADMIN)


class IsOwnerOrAdminOrStaff(RolePermission):
    roles = (
        AccountMembershipRole.OWNER,
        AccountMembershipRole.ADMIN,
        AccountMembershipRole.STAFF,
    )


class IsManagementAdminOrStaff(BasePermission):
    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        return bool(user and user.is_authenticated and getattr(user, "is_staff", False))


class IsManagementAdmin(IsManagementAdminOrStaff):
    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        return bool(
            user
            and user.is_authenticated
            and getattr(user, "is_staff", False)
            and getattr(user, "is_superuser", False)
        )

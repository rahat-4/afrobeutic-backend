from rest_framework.permissions import BasePermission

from apps.authentication.models import AccountMembership
from apps.authentication.choices import AccountMembershipRole


class IsManagementAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_staff
            and AccountMembership.objects.filter(
                user=request.user, role=AccountMembershipRole.MANAGEMENT_ADMIN
            ).exists()
        )


class IsManagementStaff(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_staff
            and AccountMembership.objects.filter(
                user=request.user, role=AccountMembershipRole.MANAGEMENT_STAFF
            ).exists()
        )


class IsOwner(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and AccountMembership.objects.filter(
                user=request.user, role=AccountMembershipRole.OWNER
            ).exists()
        )


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and AccountMembership.objects.filter(
                user=request.user, role=AccountMembershipRole.ADMIN
            ).exists()
        )


class IsStaff(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and AccountMembership.objects.filter(
                user=request.user, role=AccountMembershipRole.STAFF
            ).exists()
        )


class IsOwnerOrAdmin(BasePermission):

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and AccountMembership.objects.filter(
                user=request.user,
                role__in=[AccountMembershipRole.OWNER, AccountMembershipRole.ADMIN],
            ).exists()
        )

    # def has_object_permission(self, request, view, obj):
    #     logger.info(
    #         f"Checking object permissions for user {request.user} on object {obj}"
    #     )

    #     # Get the user's membership for this specific account
    #     membership = AccountMembership.objects.filter(
    #         user=request.user,
    #         account=obj.account,
    #         role__in=[AccountMembershipRole.OWNER, AccountMembershipRole.ADMIN],
    #     ).first()

    #     if not membership:
    #         return False

    #     # If the user is trying to update `status`, they must be the OWNER
    #     if request.method in ["PUT", "PATCH"] and "status" in request.data:
    #         return membership.role == AccountMembershipRole.OWNER

    #     # Otherwise allow if they are OWNER or ADMIN
    #     return True


class IsOwnerOrAdminOrStaff(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and AccountMembership.objects.filter(
                user=request.user,
                role__in=[
                    AccountMembershipRole.OWNER,
                    AccountMembershipRole.ADMIN,
                    AccountMembershipRole.STAFF,
                ],
            ).exists()
        )

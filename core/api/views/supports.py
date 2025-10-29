from rest_framework.generics import ListCreateAPIView

from common.permissions import IsOwnerOrAdminOrStaff, IsOwnerOrAdmin

from apps.support.models import SupportTicket

from ..serializers.supports import SupportTicketSerializer


class SupportTicketListView(ListCreateAPIView):
    serializer_class = SupportTicketSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            self.permission_classes = [IsOwnerOrAdmin]
        else:
            self.permission_classes = [IsOwnerOrAdminOrStaff]

        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        account = self.request.account

        return SupportTicket.objects.filter(
            account=account, account__members__user=user
        )

    def perform_create(self, serializer):
        account = self.request.account
        serializer.save(account=account)

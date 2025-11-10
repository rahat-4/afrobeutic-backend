from rest_framework.generics import ListCreateAPIView, RetrieveDestroyAPIView

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


class SupportTicketDetailView(RetrieveDestroyAPIView):
    serializer_class = SupportTicketSerializer
    permission_classes = [IsOwnerOrAdminOrStaff]

    def get_permissions(self):
        if self.request.method in ["DELETE"]:
            self.permission_classes = [IsOwnerOrAdmin]
        else:
            self.permission_classes = [IsOwnerOrAdminOrStaff]

        return super().get_permissions()

    def get_object(self):
        user = self.request.user
        account = self.request.account
        uid = self.kwargs.get("support_ticket_uid")

        return SupportTicket.objects.get(
            uid=uid, account=account, account__members__user=user
        )

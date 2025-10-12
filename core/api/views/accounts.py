from rest_framework.generics import ListCreateAPIView

from apps.authentication.models import Account, AccountMembership

from ..serializers.accounts import AccountSerializer


class AccountListView(ListCreateAPIView):
    serializer_class = AccountSerializer

    def get_queryset(self):
        user = self.request.user
        return Account.objects.filter(members__user=user)

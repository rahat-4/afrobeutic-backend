from datetime import timedelta
from urllib.parse import urlencode

from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect
from django.utils import timezone

from rest_framework import status
from rest_framework.generics import ListCreateAPIView
from rest_framework.views import APIView
from rest_framework.response import Response

from apps.authentication.models import Account, AccountMembership, AccountInvitation

from apps.authentication.emails import (
    send_verification_email,
    send_account_invitation_email,
)

from common.permissions import IsOwnerOrAdmin

from ..serializers.accounts import (
    AccountSerializer,
    AccountInvitationSerializer,
)


User = get_user_model()


class AccountListView(ListCreateAPIView):
    serializer_class = AccountSerializer

    def get_queryset(self):
        user = self.request.user
        return Account.objects.filter(members__user=user)


class AccountInvitationView(APIView):
    serializer_class = AccountInvitationSerializer
    permission_classes = [IsOwnerOrAdmin]
    throttle_scope = "invite"

    def post(self, request):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        invitation = serializer.save(
            invited_by=request.user,
            account=request.user.memberships.first().account,
            expires_at=timezone.now() + timedelta(minutes=60),
        )

        # Send invitation email
        send_account_invitation_email(invitation)

        return Response(
            {"message": "Account invitation sent.", "expires_in_minutes": 60},
            status=status.HTTP_200_OK,
        )

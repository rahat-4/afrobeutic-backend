from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import (
    ListAPIView,
    UpdateAPIView,
    RetrieveUpdateAPIView,
    RetrieveUpdateDestroyAPIView,
)

from apps.authentication.models import Account, AccountMembership

from apps.billing.models import PaymentTransaction
from apps.billing.choices import PaymentTransactionStatus, SubscriptionStatus
from apps.billing.utils import (
    get_or_create_stripe_customer,
    attach_payment_method,
    charge_customer,
)

from apps.authentication.emails import send_account_invitation_email

from common.permissions import IsOwner, IsOwnerOrAdmin, IsOwnerOrAdminOrStaff

from ..serializers.accounts import (
    AccountAccessSerializer,
    AccountInvitationSerializer,
    AccountMemberSerializer,
    AccountSubscriptionSerializer,
)


User = get_user_model()


class AccountMemberListView(ListAPIView):
    serializer_class = AccountMemberSerializer
    permission_classes = [IsOwnerOrAdminOrStaff]

    def get_queryset(self):
        account = self.request.account
        return AccountMembership.objects.filter(account=account)


class AccountMemberDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = AccountMemberSerializer
    permission_classes = [IsOwner]

    def get_object(self):
        account = self.request.account
        member_uid = self.kwargs.get("member_uid")
        return AccountMembership.objects.get(account=account, uid=member_uid)


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


class AccountAccessListView(ListAPIView):
    serializer_class = AccountAccessSerializer

    def get_queryset(self):
        user = self.request.user
        return Account.objects.filter(members__user=user)




class AccountSubscriptionDetailView(UpdateAPIView):
    serializer_class = AccountSubscriptionSerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_object(self):
        return self.request.account.account_subscription

    def perform_update(self, serializer):
        account = self.request.account
        subscription = self.get_object()

        pricing_plan = serializer.validated_data["pricing_plan"]
        payment_method_id = serializer.validated_data["payment_method_id"]

        customer_id = get_or_create_stripe_customer(account)

        attach_payment_method(customer_id, payment_method_id)

        print(f"================= Creating PaymentIntent for customer {customer_id} =================")
        intent = charge_customer(
            customer_id,
            payment_method_id,
            pricing_plan.price,
        )
        print(f"================= PaymentIntent created: {intent.id}, status: {intent.status} =================")

        # Save transaction (PENDING, webhook will finalize)
        PaymentTransaction.objects.create(
            account=account,
            subscription=subscription,
            amount=pricing_plan.price,
            currency="USD",
            transaction_id=intent.id,
            status=PaymentTransactionStatus.PENDING,
            payment_method=payment_method_id,
        )

        subscription.pricing_plan = pricing_plan
        subscription.status = SubscriptionStatus.PENDING
        subscription.save(update_fields=["pricing_plan", "status"])
        
        print(f"================= Transaction saved with ID: {intent.id}, awaiting webhook =================")

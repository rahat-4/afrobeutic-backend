from datetime import timedelta
from decouple import config

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import (
    ListAPIView,
    RetrieveAPIView,
    RetrieveUpdateAPIView,
    RetrieveUpdateDestroyAPIView,
)

from apps.authentication.models import Account, AccountMembership

from apps.billing.models import PricingPlan, PaymentTransaction
from apps.billing.choices import PaymentTransactionStatus, SubscriptionStatus
from apps.billing.utils import (
    get_or_create_stripe_customer,
    attach_payment_method,
    charge_customer,
)
from apps.authentication.emails import send_account_invitation_email
from apps.thirdparty.models import MetaConfig
from apps.thirdparty.utils import create_twilio_subaccount

from common.crypto import encrypt_data, decrypt_data
from common.permissions import IsOwner, IsOwnerOrAdmin, IsOwnerOrAdminOrStaff

from ..serializers.accounts import (
    AccountAccessSerializer,
    AccountInvitationSerializer,
    AccountMemberSerializer,
    AccountPricingPlanSerializer,
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


class AccountPricingPlanListView(ListAPIView):
    queryset = PricingPlan.objects.filter(is_active=True)
    serializer_class = AccountPricingPlanSerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_queryset(self):
        account = self.request.account

        return (
            super()
            .get_queryset()
            .filter(account_category=account.account_type)
            .order_by("price")
        )


class AccountPricingPlanDetailView(RetrieveAPIView):
    serializer_class = AccountPricingPlanSerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_object(self):
        uid = self.kwargs.get("pricing_plan_uid")

        try:
            pricing_plan = PricingPlan.objects.get(uid=uid)
            return pricing_plan
        except PricingPlan.DoesNotExist:
            raise ValidationError("Pricing plan not found.")


class AccountSubscriptionDetailView(RetrieveUpdateAPIView):
    serializer_class = AccountSubscriptionSerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_object(self):
        return self.request.account.account_subscription

    def perform_update(self, serializer):
        with transaction.atomic():
            account = self.request.account
            subscription = self.get_object()

            pricing_plan = serializer.validated_data["pricing_plan"]
            payment_method_id = serializer.validated_data["payment_method_id"]
            auto_renew = serializer.validated_data.get(
                "auto_renew", subscription.auto_renew
            )

            customer_id = get_or_create_stripe_customer(account)

            attach_payment_method(customer_id, payment_method_id)

            intent = charge_customer(
                customer_id,
                payment_method_id,
                pricing_plan.price,
            )

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
            subscription.auto_renew = auto_renew
            subscription.save(update_fields=["pricing_plan", "status", "auto_renew"])


class AccountMetaConfigView(APIView):
    permission_classes = [IsOwnerOrAdmin]

    def get_crypto_password(self):
        return config("CRYPTO_PASSWORD")

    def decrypt_meta_config(self, meta_config):
        crypto_password = self.get_crypto_password()
        return {
            "waba_id": decrypt_data(meta_config.waba_id, crypto_password),
            "account_sid": decrypt_data(meta_config.account_sid, crypto_password),
            "auth_token": decrypt_data(meta_config.auth_token, crypto_password),
        }

    def encrypt_meta_config(self, waba_id, account_sid, auth_token):
        crypto_password = self.get_crypto_password()
        return {
            "waba_id": encrypt_data(waba_id, crypto_password),
            "account_sid": encrypt_data(account_sid, crypto_password),
            "auth_token": encrypt_data(auth_token, crypto_password),
        }

    def get(self, request):
        meta_config = getattr(request.account, "account_meta_config", None)

        if not meta_config:
            return Response(
                {"error": "Meta configuration not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            self.decrypt_meta_config(meta_config),
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        account = request.account
        waba_id = request.data.get("waba_id")

        if not waba_id:
            return Response(
                {"error": "Missing waba_id"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Prevent duplicate creation
        if hasattr(account, "account_meta_config"):
            return Response(
                {"error": "Meta configuration already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            subaccount = create_twilio_subaccount(friendly_name=account.name)

            encrypted_data_dict = self.encrypt_meta_config(
                waba_id=waba_id,
                account_sid=subaccount["account_sid"],
                auth_token=subaccount["auth_token"],
            )

            MetaConfig.objects.create(
                account=account,
                **encrypted_data_dict,
            )

        return Response(
            {"message": "Meta configuration created successfully."},
            status=status.HTTP_201_CREATED,
        )

    def delete(self, request):
        account = request.account

        if not hasattr(account, "account_meta_config"):
            return Response(
                {"error": "Meta configuration not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        account.account_meta_config.delete()

        return Response(
            {"message": "Meta configuration deleted successfully."},
            status=status.HTTP_200_OK,
        )

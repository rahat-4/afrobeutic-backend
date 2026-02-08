from datetime import timedelta

from django.contrib.auth import get_user_model
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

from apps.thirdparty.utils import (
    create_twilio_subaccount,
    create_whatsapp_sender,
    configure_subaccount,
)

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


class AccountWhatsappOnboardView(APIView):
    """
    Receives Embedded Signup result from frontend and registers the sender with Twilio.
    """

    permission_classes = []

    def post(self, request):

        print("------------------------------->", request.data)
        waba_id = request.data.get("waba_id")
        phone_number_id = request.data.get("phone_number_id")
        phone_number = request.data.get("phone_number")

        if not waba_id or not phone_number_id:
            return Response(
                {"error": "Missing waba_id or phone_number"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create a subaccount for the salon
        subaccount = create_twilio_subaccount(friendly_name=request.account.name)

        print("-------------------------------> Subaccount created:", subaccount)
        # configure_subaccount(
        #     subaccount_sid=subaccount["account_sid"],
        #     subaccount_auth_token=subaccount["auth_token"],
        # )

        # Register whatsapp sender on Twilio
        from twilio.rest import Client
        from twilio.rest.messaging.v2 import ChannelsSenderList
        from django.conf import settings

        client = Client(subaccount["account_sid"], subaccount["auth_token"])
        # client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        sender = client.messaging.v2.channels_senders.create(
            messaging_v2_channels_sender_requests_create=ChannelsSenderList.MessagingV2ChannelsSenderRequestsCreate(
                {
                    "sender_id": "whatsapp:+15557808321",
                    "configuration": ChannelsSenderList.MessagingV2ChannelsSenderConfiguration(
                        {
                            "waba_id": waba_id,
                        }
                    ),
                    "profile": ChannelsSenderList.MessagingV2ChannelsSenderProfile(
                        {"name": "New"}
                    ),
                    "webhook": ChannelsSenderList.MessagingV2ChannelsSenderWebhook(
                        {
                            "callback_url": "https://api.afrobeutic.com/webhooks/whatsapp-callback",
                            "callback_method": "POST",
                            "fallback_url": "https://api.afrobeutic.com/webhooks/whatsapp-fallback",
                            "fallback_method": "POST",
                            "status_callback_url": "https://api.afrobeutic.com/webhooks/whatsapp-callback-status",
                            "status_callback_method": "POST",
                        }
                    ),
                }
            )
        )

        # sender = client.messaging.v2.channels_senders(
        #     "XE35e8b67cdafe341baa0538b36df1b4e6"
        # ).fetch()

        # channels_sender = client.messaging.v2.channels_senders(
        #     "XEc717e665dcac124be015b41be68ac7f8"
        # ).update(
        #     messaging_v2_channels_sender_requests_update=ChannelsSenderList.MessagingV2ChannelsSenderRequestsUpdate(
        #         {
        #             "webhook": ChannelsSenderList.MessagingV2ChannelsSenderWebhook(
        #                 {
        #                     "callback_url": "https://api.afrobeutic.com/webhooks/whatsapp-callback",
        #                     "callback_method": "POST",
        #                     "fallback_url": "https://api.afrobeutic.com/webhooks/whatsapp-fallback",
        #                     "fallback_method": "POST",
        #                     "status_callback_url": "https://api.afrobeutic.com/webhooks/whatsapp-callback-status",
        #                     "status_callback_method": "POST",
        #                 }
        #             )
        #         }
        #     )
        # )

        # sender = create_whatsapp_sender(
        #     subaccount_sid=subaccount["account_sid"],
        #     subaccount_auth_token=subaccount["auth_token"],
        #     waba_id=waba_id,
        #     phone_number_id=phone_number_id,
        #     phone_number=phone_number,
        # )
        print("-------------------------------> Sender registered:", sender.sid)

        # sender_sid = sender.get("sid") or sender.get("Sid")
        # sender_status = sender.get("status") or sender.get("Status")

        return Response(
            {
                "message": "WhatsApp sender registered successfully",
                "account": request.account.name,
                "sender_sid": sender.sid,
                "sender_status": sender.status,
            },
            status=status.HTTP_201_CREATED,
        )

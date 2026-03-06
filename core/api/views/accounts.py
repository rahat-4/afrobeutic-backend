import stripe
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import (
    ListAPIView,
    ListCreateAPIView,
    RetrieveAPIView,
    RetrieveUpdateAPIView,
    RetrieveUpdateDestroyAPIView,
)

from apps.authentication.models import Account, AccountMembership

from apps.billing.models import PricingPlan, PaymentTransaction, PaymentCard
from apps.billing.choices import PaymentTransactionStatus, SubscriptionStatus
from apps.billing.utils import (
    get_or_create_stripe_customer,
    charge_customer,
)
from apps.authentication.emails import send_account_invitation_email
from apps.salon.models import Booking
from apps.salon.models import BookingStatus
from apps.support.models import AccountSupportTicket


from common.permissions import IsOwner, IsOwnerOrAdmin, IsOwnerOrAdminOrStaff

from ..serializers.accounts import (
    AccountAccessSerializer,
    AccountInvitationSerializer,
    AccountMemberSerializer,
    AccountPricingPlanSerializer,
    AccountSubscriptionSerializer,
    AccountBillingHistorySerializer,
    AccountPaymentCardSerializer,
)

stripe.api_key = settings.STRIPE_SECRET_KEY
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

            pricing_plan = serializer.validated_data.get("pricing_plan")
            payment_card = serializer.validated_data.get("payment_card")
            auto_renew = serializer.validated_data.get(
                "auto_renew", subscription.auto_renew
            )

            # Case 1: Only auto_renew update
            if pricing_plan is None:
                subscription.auto_renew = auto_renew
                subscription.save(update_fields=["auto_renew"])
                return

            customer_id = get_or_create_stripe_customer(account)

            # Use saved card token
            payment_method_id = payment_card.card_token

            intent = charge_customer(
                customer_id,
                payment_method_id,
                pricing_plan.price,
            )

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


class AccountBillingHistoryListView(ListAPIView):
    serializer_class = AccountBillingHistorySerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_queryset(self):
        return PaymentTransaction.objects.filter(
            account=self.request.account
        ).select_related("subscription__pricing_plan")


class AccountPaymentCardListView(ListCreateAPIView):
    serializer_class = AccountPaymentCardSerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_queryset(self):
        return PaymentCard.objects.filter(account=self.request.account)

    def perform_create(self, serializer):
        account = self.request.account
        payment_method_id = serializer.validated_data.pop("payment_method_id")

        if not payment_method_id:
            raise ValidationError("payment_method_id is required.")

        customer_id = get_or_create_stripe_customer(account)

        stripe.PaymentMethod.attach(
            payment_method_id,
            customer=customer_id,
        )

        payment_method = stripe.PaymentMethod.retrieve(payment_method_id)

        is_first_card = not account.account_payment_cards.exists()

        card = serializer.save(
            account=account,
            card_token=payment_method_id,
            last_four=payment_method.card.last4,
            card_brand=payment_method.card.brand,
            expiry_month=payment_method.card.exp_month,
            expiry_year=payment_method.card.exp_year,
            is_default=is_first_card,
        )

        if is_first_card:
            stripe.Customer.modify(
                customer_id,
                invoice_settings={"default_payment_method": payment_method_id},
            )


class AccountPaymentCardDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = AccountPaymentCardSerializer
    permission_classes = [IsOwnerOrAdmin]
    lookup_field = "uid"
    lookup_url_kwarg = "card_uid"

    def get_queryset(self):
        return PaymentCard.objects.filter(account=self.request.account)

    def perform_destroy(self, instance):
        account = self.request.account
        was_default = instance.is_default

        stripe.PaymentMethod.detach(instance.card_token)
        instance.delete()

        if was_default:
            new_default = account.account_payment_cards.first()
            if new_default:
                new_default.is_default = True
                new_default.save(update_fields=["is_default"])

                stripe.Customer.modify(
                    account.stripe_customer_id,
                    invoice_settings={"default_payment_method": new_default.card_token},
                )


# GET /api/dashboard/?bookings_filter=last_7_days
# GET /api/dashboard/?bookings_filter=last_30_days
# GET /api/dashboard/?income_filter=this_month
# GET /api/dashboard/?requests_filter=this_year
# GET /api/dashboard/?clients_filter=all_time
class AccountDashboardApiView(APIView):
    permission_classes = [IsOwnerOrAdminOrStaff]

    def get_date_range(self, filter_type):
        today = timezone.now().date()

        if filter_type == "last_7_days":
            return today - timedelta(days=7), today
        elif filter_type == "last_30_days":
            return today - timedelta(days=30), today
        elif filter_type == "this_month":
            return today.replace(day=1), today
        elif filter_type == "this_year":
            return today.replace(month=1, day=1), today
        elif filter_type == "all_time":
            return None, None

        return today - timedelta(days=7), today

    def apply_date_filter(self, queryset, field, start_date, end_date):
        if start_date and end_date:
            return queryset.filter(**{f"{field}__range": (start_date, end_date)})
        return queryset

    def get(self, request):
        account = request.account

        # Separate filters for each card
        bookings_filter = request.query_params.get("bookings_filter", "last_7_days")
        income_filter = request.query_params.get("income_filter", "last_7_days")
        requests_filter = request.query_params.get("requests_filter", "last_7_days")
        clients_filter = request.query_params.get("clients_filter", "last_7_days")

        # ==========================
        # CARD 1 - BOOKINGS
        # ==========================
        bookings = Booking.objects.filter(account=account)
        start, end = self.get_date_range(bookings_filter)
        bookings = self.apply_date_filter(bookings, "booking_date", start, end)

        total_bookings = bookings.count()

        completed_bookings = bookings.filter(status=BookingStatus.COMPLETED)
        completed_count = completed_bookings.count()

        completion_rate = (
            round((completed_count / total_bookings) * 100, 2)
            if total_bookings > 0
            else 0
        )

        # ==========================
        # CARD 2 - INCOME
        # ==========================
        income_bookings = Booking.objects.filter(
            account=account, status=BookingStatus.COMPLETED
        )
        start, end = self.get_date_range(income_filter)
        income_bookings = self.apply_date_filter(
            income_bookings, "booking_date", start, end
        )

        total_income = Decimal("0.00")

        for booking in income_bookings.prefetch_related("services", "products"):
            for service in booking.services.all():
                total_income += service.final_price()

            for product in booking.products.all():
                total_income += product.price

            total_income += booking.tips_amount or Decimal("0.00")

        total_income = total_income.quantize(Decimal("0.01"))

        # ==========================
        # CARD 3 - CLIENT REQUESTS
        # ==========================
        client_requests = AccountSupportTicket.objects.filter(account=account)
        start, end = self.get_date_range(requests_filter)
        client_requests = self.apply_date_filter(
            client_requests, "created_at__date", start, end
        )

        client_requests_count = client_requests.count()

        # ==========================
        # CARD 4 - TOTAL CLIENTS
        # ==========================
        clients_bookings = Booking.objects.filter(account=account)
        start, end = self.get_date_range(clients_filter)
        clients_bookings = self.apply_date_filter(
            clients_bookings, "booking_date", start, end
        )

        total_clients = clients_bookings.values("customer").distinct().count()

        return Response(
            {
                "card_1": {
                    "total_bookings": total_bookings,
                    "booking_completion_rate": completion_rate,
                },
                "card_2": {
                    "total_income": total_income,
                },
                "card_3": {
                    "client_requests": client_requests_count,
                },
                "card_4": {
                    "total_clients": total_clients,
                },
            }
        )

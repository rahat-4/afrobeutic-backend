import stripe

from django.contrib.auth import get_user_model

from django.conf import settings
from django.db import transaction


from rest_framework import serializers

from apps.authentication.models import Account, AccountInvitation, AccountMembership
from apps.billing.models import (
    Subscription,
    PricingPlan,
    PaymentTransaction,
    PaymentCard,
)

from common.serializers import PricingPlanSlimSerializer

stripe.api_key = settings.STRIPE_SECRET_KEY
User = get_user_model()


class AccountMemberSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(source="user.avatar", read_only=True)
    name = serializers.CharField(source="user.get_full_name", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = AccountMembership
        fields = ["uid", "avatar", "name", "email", "role", "status"]
        read_only_fields = ["uid", "name", "email"]


class AccountInvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountInvitation
        fields = ["email", "role"]
        extra_kwargs = {
            "email": {"required": True},
            "role": {"required": True},
        }

    def validate_email(self, value):
        request = self.context.get("request")
        if request and request.user.email.lower() == value.lower():
            raise serializers.ValidationError("You cannot invite yourself.")

        # Check for existing unaccepted invitation
        account_invitation = AccountInvitation.objects.filter(
            email=value, is_accepted=False
        ).first()

        if account_invitation:
            if account_invitation.is_expired():
                account_invitation.delete()
            else:
                raise serializers.ValidationError(
                    "An invitation has already been sent to this email."
                )
        return value


class AccountAccessSerializer(serializers.ModelSerializer):
    owner_name = serializers.SerializerMethodField()
    owner_email = serializers.EmailField(source="owner.email", read_only=True)
    role = serializers.SerializerMethodField()

    class Meta:
        model = Account
        fields = ["uid", "name", "owner_name", "owner_email", "role"]

    def get_owner_name(self, obj):
        return f"{obj.owner.first_name} {obj.owner.last_name}"

    def get_role(self, obj):
        user = self.context.get("request").user
        membership = obj.members.filter(user=user).first()
        return membership.role if membership else None


class AccountPricingPlanSerializer(serializers.ModelSerializer):
    is_current_plan = serializers.SerializerMethodField()

    class Meta:
        model = PricingPlan
        fields = [
            "uid",
            "name",
            "price",
            "salon_limit",
            "whatsapp_chatbot_limit",
            "whatsapp_messages_per_chatbot",
            "description",
            "is_current_plan",
        ]

    def get_is_current_plan(self, obj):
        request = self.context.get("request")
        if not request:
            return False

        account = request.account
        subscription = getattr(account, "account_subscription", None)

        if subscription and subscription.pricing_plan.uid == obj.uid:
            return True

        return False


class AccountSubscriptionSerializer(serializers.ModelSerializer):
    pricing_plan = serializers.SlugRelatedField(
        slug_field="uid",
        queryset=PricingPlan.objects.all(),
        write_only=True,
    )

    payment_card = serializers.SlugRelatedField(
        slug_field="uid",
        queryset=PaymentCard.objects.all(),
        write_only=True,
    )

    class Meta:
        model = Subscription
        fields = [
            "status",
            "start_date",
            "end_date",
            "next_billing_date",
            "auto_renew",
            "cancelled_at",
            "notes",
            "pricing_plan",
            "payment_card",
        ]

        read_only_fields = [
            "status",
            "start_date",
            "end_date",
            "next_billing_date",
            "cancelled_at",
        ]

    def validate_payment_card(self, value):
        request = self.context["request"]

        if value.account != request.account:
            raise serializers.ValidationError("Invalid payment card.")

        return value

    def validate(self, attrs):
        request = self.context["request"]
        account = request.account
        new_plan = attrs.get("pricing_plan")

        if not new_plan:
            return attrs

        try:
            current_sub = account.account_subscription
            current_plan = current_sub.pricing_plan
        except Subscription.DoesNotExist:
            return attrs

        # ── Collect current resource usage ────────────────────────────────────
        current_salon_count = account.account_salons.count()
        current_chatbot_count = account.account_chatbot_config.filter(
            is_active=True
        ).count()

        downgrade_errors = []

        # ── Salon limit check ─────────────────────────────────────────────────
        if new_plan.salon_limit < current_salon_count:
            excess = current_salon_count - new_plan.salon_limit
            downgrade_errors.append(
                f"{current_salon_count} salon(s) active — new plan allows "
                f"{new_plan.salon_limit}. Please delete {excess} salon(s) first."
            )

        # ── Chatbot limit check ───────────────────────────────────────────────
        if new_plan.whatsapp_chatbot_limit < current_chatbot_count:
            excess = current_chatbot_count - new_plan.whatsapp_chatbot_limit
            downgrade_errors.append(
                f"{current_chatbot_count} chatbot(s) active — new plan allows "
                f"{new_plan.whatsapp_chatbot_limit}. Please delete {excess} chatbot(s) first."
            )

        if downgrade_errors:
            # Bundle all resource conflicts into one clear error
            detail = f"Cannot switch to '{new_plan.name}': " + " ".join(
                downgrade_errors
            )
            raise serializers.ValidationError({"downgrade_warning": detail})

        return attrs

    def to_representation(self, instance):
        from common.serializers import PricingPlanSlimSerializer

        rep = super().to_representation(instance)
        rep["pricing_plan"] = PricingPlanSlimSerializer(instance.pricing_plan).data
        rep["remaining_messages"] = self._get_remaining_messages(instance)
        return rep

    def _get_remaining_messages(self, instance):
        """
        Total remaining = messages already used subtracted from the
        STACKED pool (carried-over balance + new plan allowance).
        Stored on the subscription so it survives plan changes.
        """
        return getattr(instance, "remaining_whatsapp_messages", None)


class AccountBillingHistorySerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(
        source="subscription.pricing_plan.name", read_only=True
    )
    invoice_url = serializers.SerializerMethodField()
    transaction_status = serializers.SerializerMethodField()

    class Meta:
        model = PaymentTransaction
        fields = [
            "plan_name",
            "transaction_status",
            "amount",
            "created_at",
            "invoice_url",
        ]

    def get_transaction_status(self, obj):
        if obj.status == "SUCCEEDED":
            return "Paid"
        return "Invalid"

    def get_invoice_url(self, obj):
        if obj.status != "SUCCEEDED":
            return None

        try:
            intent = stripe.PaymentIntent.retrieve(obj.transaction_id)

            if intent.charges and intent.charges.data:
                return intent.charges.data[0].receipt_url

            return None
        except Exception:
            return None


class AccountPaymentCardSerializer(serializers.ModelSerializer):
    payment_method_id = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = PaymentCard
        fields = [
            "uid",
            "card_brand",
            "last_four",
            "expiry_month",
            "expiry_year",
            "is_default",
            "payment_method_id",
        ]
        read_only_fields = [
            "uid",
            "card_brand",
            "last_four",
            "expiry_month",
            "expiry_year",
        ]

    def update(self, instance, validated_data):
        request = self.context["request"]
        account = request.account

        is_default = validated_data.get("is_default", None)

        with transaction.atomic():
            # If setting this card as default
            if is_default is True:

                # Unset all other cards
                PaymentCard.objects.filter(account=account).update(is_default=False)

                instance.is_default = True
                instance.save(update_fields=["is_default"])

                # Sync with Stripe
                stripe.Customer.modify(
                    account.stripe_customer_id,
                    invoice_settings={"default_payment_method": instance.card_token},
                )

            # Prevent manually unsetting default card
            elif is_default is False and instance.is_default:
                raise serializers.ValidationError(
                    {"is_default": "You cannot unset the default card directly."}
                )

        return instance

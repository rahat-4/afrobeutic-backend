from datetime import timedelta
import stripe

from django.conf import settings
from django.utils import timezone

from apps.authentication.models import Account
from apps.billing.models import PaymentTransaction
from apps.billing.choices import SubscriptionStatus, PaymentTransactionStatus

stripe.api_key = settings.STRIPE_SECRET_KEY


def get_or_create_stripe_customer(account):
    if account.stripe_customer_id:
        return account.stripe_customer_id

    customer = stripe.Customer.create(
        email=account.owner.email,
        name=account.owner.get_full_name(),
    )
    account.stripe_customer_id = customer.id
    account.save(update_fields=["stripe_customer_id"])
    return customer.id


def attach_payment_method(customer_id, payment_method_id):
    stripe.PaymentMethod.attach(
        payment_method_id,
        customer=customer_id,
    )

    stripe.Customer.modify(
        customer_id,
        invoice_settings={
            "default_payment_method": payment_method_id,
        },
    )


def charge_customer(customer_id, payment_method_id, amount):
    # Stripe minimum charge is $0.50 for USD
    if amount < 0.50:
        raise ValueError(f"Amount ${amount} is below Stripe's minimum charge amount of $0.50 USD")
    
    print(f"Charging customer {customer_id} amount: ${amount} ({int(amount * 100)} cents)")
    
    return stripe.PaymentIntent.create(
        amount=int(amount * 100),
        currency="usd",
        customer=customer_id,
        payment_method=payment_method_id,
        off_session=True,
        confirm=True,
    )


def handle_payment_success(payment_intent):
    print("------------------ Handling Payment Success ------------------")
    customer_id = payment_intent["customer"]
    transaction_id = payment_intent["id"]

    try:
        account = Account.objects.get(stripe_customer_id=customer_id)
        subscription = account.account_subscription
        transaction = PaymentTransaction.objects.get(transaction_id=transaction_id)
    except Exception:
        return

    transaction.status = PaymentTransactionStatus.SUCCEEDED
    transaction.save(update_fields=["status"])

    subscription.status = SubscriptionStatus.ACTIVE
    subscription.start_date = timezone.now()
    subscription.end_date = subscription.start_date + timedelta(days=30)
    subscription.next_billing_date = subscription.end_date
    subscription.save()


def handle_payment_failed(payment_intent):
    print("------------------ Handling Payment Failed ------------------")
    customer_id = payment_intent["customer"]
    transaction_id = payment_intent["id"]

    try:
        account = Account.objects.get(stripe_customer_id=customer_id)
        subscription = account.account_subscription
        transaction = PaymentTransaction.objects.get(transaction_id=transaction_id)
    except Exception:
        return

    transaction.status = PaymentTransactionStatus.FAILED
    transaction.save(update_fields=["status"])

    # Optionally update subscription status if payment failed
    # subscription.status = SubscriptionStatus.PAST_DUE
    # subscription.save(update_fields=["status"])

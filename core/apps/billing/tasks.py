"""
apps/billing/tasks.py

One daily Celery beat task:
  - process_auto_renewals: charge due subscriptions.
    Success → renew + email.
    Failure → cancel + disable chatbots + email.
"""

import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from apps.billing.choices import PaymentTransactionStatus, SubscriptionStatus
from apps.billing.models import PaymentTransaction, Subscription
from apps.billing.utils import charge_customer, get_or_create_stripe_customer

from common.email_notifications import (
    send_trial_expiry_warning_email,
    send_upcoming_renewal_reminder_email,
    send_renewal_success_email,
    send_renewal_failed_email,
)

logger = logging.getLogger(__name__)


@shared_task(name="apps.billing.tasks.process_auto_renewals")
def process_auto_renewals():
    now = timezone.now()

    due_subscriptions = Subscription.objects.filter(
        auto_renew=True,
        status=SubscriptionStatus.ACTIVE,
        next_billing_date__lte=now,
    ).select_related("pricing_plan", "account__owner")

    logger.info("Auto-renewal: %d subscription(s) due.", due_subscriptions.count())

    for subscription in due_subscriptions:
        with transaction.atomic():
            account = subscription.account
            default_card = account.account_payment_cards.filter(is_default=True).first()

            if not default_card:
                logger.warning(
                    "No default card for account %s — cancelling.", account.name
                )
                _cancel(subscription)
                send_renewal_failed_email(subscription)
                continue

            try:
                # ── Attempt charge ────────────────────────────────────────────
                customer_id = get_or_create_stripe_customer(account)
                intent = charge_customer(
                    customer_id,
                    default_card.card_token,
                    subscription.pricing_plan.price,
                )

                PaymentTransaction.objects.create(
                    account=account,
                    subscription=subscription,
                    amount=subscription.pricing_plan.price,
                    currency="USD",
                    transaction_id=intent.id,
                    status=PaymentTransactionStatus.SUCCESS,
                    payment_method=default_card.card_token,
                )

                # ── Renew ─────────────────────────────────────────────────────
                _renew(subscription)
                send_renewal_success_email(subscription)
                logger.info("Renewed subscription for account: %s", account.name)

            except Exception as exc:
                logger.warning("Payment failed for account %s: %s", account.name, exc)

                PaymentTransaction.objects.create(
                    account=account,
                    subscription=subscription,
                    amount=subscription.pricing_plan.price,
                    currency="USD",
                    transaction_id=f"failed_{account.pk}_{now.timestamp()}",
                    status=PaymentTransactionStatus.FAILED,
                    payment_method=default_card.card_token,
                )

                # ── Cancel + disable chatbots ──────────────────────────────────
                _cancel(subscription)
                send_renewal_failed_email(subscription)
                logger.warning("Subscription cancelled for account: %s", account.name)


# ─────────────────────────────────────────────────────────────────────────────
# State helpers
# ─────────────────────────────────────────────────────────────────────────────


def _renew(subscription: Subscription) -> None:
    """Successful renewal: stack messages, push next billing date, re-enable chatbots."""
    now = timezone.now()

    # Stack: carry over remaining + new plan pool
    new_remaining = (
        subscription.remaining_whatsapp_messages
        + subscription.pricing_plan.total_messages
    )

    subscription.status = SubscriptionStatus.ACTIVE
    subscription.remaining_whatsapp_messages = new_remaining
    subscription.start_date = now
    subscription.end_date = now + timezone.timedelta(days=30)
    subscription.next_billing_date = subscription.end_date
    subscription.save(
        update_fields=[
            "status",
            "remaining_whatsapp_messages",
            "start_date",
            "end_date",
            "next_billing_date",
        ]
    )

    # Re-enable all chatbots for this account
    subscription.account.whatsapp_chatbot_configs.update(is_active=True)


def _cancel(subscription: Subscription) -> None:
    """Failed payment: cancel subscription and disable all chatbots."""
    subscription.status = SubscriptionStatus.CANCELLED
    subscription.auto_renew = False
    subscription.cancelled_at = timezone.now()
    subscription.save(update_fields=["status", "auto_renew", "cancelled_at"])

    # Disable all chatbots immediately
    subscription.account.whatsapp_chatbot_configs.update(is_active=False)


"""
apps/billing/tasks.py  (reminder tasks — add to existing tasks.py)

Two new daily Celery beat tasks:
  - send_renewal_reminders   : fires 2 days before next_billing_date (ACTIVE subs)
  - send_trial_expiry_warnings: fires 2 days before end_date (TRIAL subs)
"""


@shared_task(name="apps.billing.tasks.send_renewal_reminders")
def send_renewal_reminders():
    """
    Runs daily. Finds ACTIVE subscriptions whose next_billing_date
    is exactly 2 days away and sends a reminder email.
    """
    now = timezone.now()
    target_date = (now + timezone.timedelta(days=2)).date()

    subscriptions = Subscription.objects.filter(
        status=SubscriptionStatus.ACTIVE,
        auto_renew=True,
        next_billing_date__date=target_date,
    ).select_related("pricing_plan", "account__owner")

    for subscription in subscriptions:
        try:
            send_upcoming_renewal_reminder_email(subscription)
        except Exception as exc:
            import logging

            logging.getLogger(__name__).warning(
                "Failed to send renewal reminder for account %s: %s",
                subscription.account.name,
                exc,
            )


@shared_task(name="apps.billing.tasks.send_trial_expiry_warnings")
def send_trial_expiry_warnings():
    """
    Runs daily. Finds TRIAL subscriptions whose end_date
    is exactly 2 days away and sends a warning email.
    """
    now = timezone.now()
    target_date = (now + timezone.timedelta(days=2)).date()

    subscriptions = Subscription.objects.filter(
        status=SubscriptionStatus.TRIAL,
        end_date__date=target_date,
    ).select_related("pricing_plan", "account__owner")

    for subscription in subscriptions:
        try:
            send_trial_expiry_warning_email(subscription)
        except Exception as exc:
            import logging

            logging.getLogger(__name__).warning(
                "Failed to send trial expiry warning for account %s: %s",
                subscription.account.name,
                exc,
            )

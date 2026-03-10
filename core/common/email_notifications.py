"""
apps/billing/emails.py
"""

from django.conf import settings
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Email, Mail

from apps.billing.models import Subscription


def _send(message: Mail) -> bool:
    message.reply_to = Email("raptortech2025@gmail.com")
    try:
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        print(f"Email sent: {response.status_code}")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def send_plan_change_success_email(
    subscription: Subscription, old_plan_name: str
) -> bool:
    owner = subscription.account.owner
    account_name = subscription.account.name
    new_plan = subscription.pricing_plan.name
    remaining = subscription.remaining_whatsapp_messages
    next_billing = (
        subscription.next_billing_date.strftime("%B %d, %Y")
        if subscription.next_billing_date
        else "N/A"
    )

    print(
        f"Sending plan change success email to {owner.email} "
        f"for account {account_name} — {old_plan_name} → {new_plan}"
    )

    message = Mail(
        from_email=settings.DEFAULT_FROM_EMAIL,
        to_emails=owner.email,
        subject="Your plan has been updated ✅",
        html_content=f"""
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #eee; border-radius: 8px; background-color: #f9f9f9;">
  <h2 style="color: #333;">Plan Updated Successfully 🎉</h2>

  <p style="font-size: 16px; color: #555;">
    Hi <strong>{owner.get_full_name()}</strong>,
  </p>

  <p style="font-size: 16px; color: #555;">
    Your subscription plan has been changed successfully.
  </p>

  <div style="background-color: #fff; border: 1px solid #e0e0e0; border-radius: 6px; padding: 16px; margin: 20px 0;">
    <table style="width: 100%; font-size: 15px; color: #444; border-collapse: collapse;">
      <tr>
        <td style="padding: 8px 0; color: #888;">Previous Plan</td>
        <td style="padding: 8px 0; text-align: right;"><strong>{old_plan_name}</strong></td>
      </tr>
      <tr>
        <td style="padding: 8px 0; color: #888;">New Plan</td>
        <td style="padding: 8px 0; text-align: right;"><strong style="color: #007bff;">{new_plan}</strong></td>
      </tr>
      <tr>
        <td style="padding: 8px 0; color: #888; border-top: 1px solid #f0f0f0;">Message Balance</td>
        <td style="padding: 8px 0; text-align: right; border-top: 1px solid #f0f0f0;"><strong>{remaining:,}</strong></td>
      </tr>
      <tr>
        <td style="padding: 8px 0; color: #888;">Next Billing Date</td>
        <td style="padding: 8px 0; text-align: right;"><strong>{next_billing}</strong></td>
      </tr>
    </table>
  </div>

  <p style="font-size: 15px; color: #555;">
    Your new plan is now active. All features and limits have been updated immediately.
  </p>

  <p style="font-size: 14px; color: #888;">
    If you did not make this change, please contact us immediately.
  </p>

  <p style="font-size: 14px; color: #888;">
    — Afrobeutic Team
  </p>
</div>
""",
    )
    return _send(message)


def send_plan_change_failed_email(account, plan_name: str) -> bool:
    owner = account.owner

    message = Mail(
        from_email=settings.DEFAULT_FROM_EMAIL,
        to_emails=owner.email,
        subject="Plan change failed — action required ❌",
        html_content=f"""
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #eee; border-radius: 8px; background-color: #f9f9f9;">
  <h2 style="color: #d9534f;">Payment Failed ❌</h2>

  <p style="font-size: 16px; color: #555;">
    Hi <strong>{owner.get_full_name()}</strong>,
  </p>

  <p style="font-size: 16px; color: #555;">
    We were unable to process your payment for the <strong>{plan_name}</strong> plan.
  </p>

  <div style="background-color: #fff3f3; border-left: 4px solid #d9534f; border-radius: 4px; padding: 14px 16px; margin: 20px 0;">
    <p style="margin: 0; font-size: 15px; color: #555;">
      Your current plan remains <strong>unchanged</strong>. No charges have been made.
    </p>
  </div>

  <p style="font-size: 15px; color: #555;">
    Please check your payment details and try again.
  </p>

  <div style="text-align: center; margin: 30px 0;">
    <a href="{settings.FRONTEND_URL}/billing"
       style="background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
      Update Payment Method
    </a>
  </div>

  <p style="font-size: 14px; color: #888;">
    If you need help, feel free to reply to this email.
  </p>

  <p style="font-size: 14px; color: #888;">
    — Afrobeutic Team
  </p>
</div>
""",
    )
    return _send(message)


def send_renewal_success_email(subscription: Subscription) -> bool:
    owner = subscription.account.owner
    remaining = subscription.remaining_whatsapp_messages
    next_billing = (
        subscription.next_billing_date.strftime("%B %d, %Y")
        if subscription.next_billing_date
        else "N/A"
    )

    message = Mail(
        from_email=settings.DEFAULT_FROM_EMAIL,
        to_emails=owner.email,
        subject="Your subscription has been renewed ✅",
        html_content=f"""
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #eee; border-radius: 8px; background-color: #f9f9f9;">
  <h2 style="color: #333;">Subscription Renewed 🎉</h2>

  <p style="font-size: 16px; color: #555;">
    Hi <strong>{owner.get_full_name()}</strong>,
  </p>

  <p style="font-size: 16px; color: #555;">
    Your <strong>{subscription.pricing_plan.name}</strong> plan has been successfully
    renewed for another 30 days.
  </p>

  <div style="background-color: #fff; border: 1px solid #e0e0e0; border-radius: 6px; padding: 16px; margin: 20px 0;">
    <table style="width: 100%; font-size: 15px; color: #444; border-collapse: collapse;">
      <tr>
        <td style="padding: 8px 0; color: #888;">Plan</td>
        <td style="padding: 8px 0; text-align: right;"><strong>{subscription.pricing_plan.name}</strong></td>
      </tr>
      <tr>
        <td style="padding: 8px 0; color: #888; border-top: 1px solid #f0f0f0;">Message Balance</td>
        <td style="padding: 8px 0; text-align: right; border-top: 1px solid #f0f0f0;"><strong>{remaining:,}</strong></td>
      </tr>
      <tr>
        <td style="padding: 8px 0; color: #888; border-top: 1px solid #f0f0f0;">Next Billing Date</td>
        <td style="padding: 8px 0; text-align: right; border-top: 1px solid #f0f0f0;"><strong>{next_billing}</strong></td>
      </tr>
    </table>
  </div>

  <p style="font-size: 14px; color: #888;">
    Thank you for staying with us!
  </p>

  <p style="font-size: 14px; color: #888;">
    — Afrobeutic Team
  </p>
</div>
""",
    )
    return _send(message)


def send_renewal_failed_email(subscription: Subscription) -> bool:
    owner = subscription.account.owner

    message = Mail(
        from_email=settings.DEFAULT_FROM_EMAIL,
        to_emails=owner.email,
        subject="Subscription payment failed — service paused ❌",
        html_content=f"""
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #eee; border-radius: 8px; background-color: #f9f9f9;">
  <h2 style="color: #d9534f;">Subscription Paused ❌</h2>

  <p style="font-size: 16px; color: #555;">
    Hi <strong>{owner.get_full_name()}</strong>,
  </p>

  <p style="font-size: 16px; color: #555;">
    We were unable to renew your <strong>{subscription.pricing_plan.name}</strong> plan.
    Your subscription has been cancelled and your WhatsApp chatbot has been paused.
  </p>

  <div style="background-color: #fff3f3; border-left: 4px solid #d9534f; border-radius: 4px; padding: 14px 16px; margin: 20px 0;">
    <p style="margin: 0; font-size: 15px; color: #555;">
      Please re-subscribe to reactivate your chatbot and restore your service.
    </p>
  </div>

  <div style="text-align: center; margin: 30px 0;">
    <a href="{settings.FRONTEND_URL}/billing"
       style="background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
      Re-subscribe Now
    </a>
  </div>

  <p style="font-size: 14px; color: #888;">
    If you need help, feel free to reply to this email.
  </p>

  <p style="font-size: 14px; color: #888;">
    — Afrobeutic Team
  </p>
</div>
""",
    )
    return _send(message)

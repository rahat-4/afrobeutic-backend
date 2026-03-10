"""
apps/billing/emails.py
"""

from django.conf import settings
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Email, Mail

from apps.billing.models import Subscription

BRAND_COLOR = "#C9A96E"  # gold accent
BRAND_DARK = "#1A1A2E"  # deep navy
BRAND_TEXT = "#4A4A6A"  # body text


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


def _base_template(title: str, body_html: str, footer_note: str = "") -> str:
    """Wraps any email body in the shared Afrobeutic branded shell."""
    return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
          <meta charset="UTF-8" />
          <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
          <title>{title}</title>
        </head>
        <body style="margin:0;padding:0;background-color:#F4F1EC;font-family:'Georgia',serif;">
          <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#F4F1EC;padding:40px 16px;">
            <tr>
              <td align="center">
                <table width="100%" cellpadding="0" cellspacing="0"
                      style="max-width:600px;background-color:#FFFFFF;border-radius:12px;
                              overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">

                  <!-- Header -->
                  <tr>
                    <td style="background-color:{BRAND_DARK};padding:32px 40px;text-align:center;">
                      <p style="margin:0;font-size:26px;font-weight:bold;color:#FFFFFF;
                                letter-spacing:3px;text-transform:uppercase;">
                        Afrobeutic
                      </p>
                      <p style="margin:6px 0 0;font-size:12px;color:{BRAND_COLOR};
                                letter-spacing:2px;text-transform:uppercase;">
                        Beauty Management Platform
                      </p>
                    </td>
                  </tr>

                  <!-- Gold divider -->
                  <tr>
                    <td style="height:4px;background:linear-gradient(90deg,{BRAND_COLOR},{BRAND_DARK},{BRAND_COLOR});"></td>
                  </tr>

                  <!-- Body -->
                  <tr>
                    <td style="padding:40px 40px 32px;">
                      {body_html}
                    </td>
                  </tr>

                  <!-- Footer -->
                  <tr>
                    <td style="background-color:#F9F7F4;padding:24px 40px;
                                border-top:1px solid #EDE9E0;text-align:center;">
                      <p style="margin:0;font-size:13px;color:#999;">
                        {footer_note or "If you have any questions, reply to this email and we&#39;ll be happy to help."}
                      </p>
                      <p style="margin:8px 0 0;font-size:12px;color:#BBB;">
                        &copy; 2025 Afrobeutic &nbsp;&middot;&nbsp; All rights reserved
                      </p>
                    </td>
                  </tr>

                </table>
              </td>
            </tr>
          </table>
        </body>
        </html>
      """


def _greeting(name: str) -> str:
    return f'<p style="margin:0 0 20px;font-size:16px;color:{BRAND_TEXT};">Hi <strong>{name}</strong>,</p>'


def _detail_row(label: str, value: str) -> str:
    return f"""
      <tr>
        <td style="padding:10px 0;font-size:14px;color:#999;border-bottom:1px solid #F0EDE8;
                    width:45%;">{label}</td>
        <td style="padding:10px 0;font-size:14px;color:{BRAND_DARK};font-weight:bold;
                    border-bottom:1px solid #F0EDE8;text-align:right;">{value}</td>
      </tr>"""


def _detail_table(rows_html: str) -> str:
    return f"""
      <table width="100%" cellpadding="0" cellspacing="0"
            style="background:#FAFAF8;border:1px solid #EDE9E0;border-radius:8px;
                    padding:0 16px;margin:20px 0;">
        {rows_html}
      </table>"""


def _cta_button(label: str, url: str, color: str = BRAND_COLOR) -> str:
    return f"""
      <div style="text-align:center;margin:32px 0;">
        <a href="{url}"
          style="background-color:{color};color:#1A1A2E;padding:14px 32px;
                  text-decoration:none;border-radius:6px;display:inline-block;
                  font-weight:bold;font-size:15px;letter-spacing:0.5px;">
          {label}
        </a>
      </div>"""


def _alert_box(text: str, color: str = "#FFF8EC", border: str = BRAND_COLOR) -> str:
    return f"""
      <div style="background-color:{color};border-left:4px solid {border};
                  border-radius:4px;padding:14px 18px;margin:20px 0;">
        <p style="margin:0;font-size:14px;color:{BRAND_TEXT};">{text}</p>
      </div>"""


# ─────────────────────────────────────────────────────────────────────────────
# 1. New Booking — to ALL account admins
# ─────────────────────────────────────────────────────────────────────────────


def send_new_booking_admin_email(booking) -> bool:
    """
    Sent to every admin in the account when a new booking is placed.
    """
    from apps.authentication.choices import AccountMembershipStatus

    customer = booking.customer
    customer_name = f"{customer.first_name} {customer.last_name}".strip()

    services = ", ".join(s.name for s in booking.services.all()) or "—"
    products = ", ".join(p.name for p in booking.products.all()) or "—"

    employee = booking.employee.name if booking.employee else "Not assigned"
    chair = booking.chair.name if booking.chair else "Not assigned"

    rows = (
        _detail_row("Booking ID", f"#{booking.booking_id}")
        + _detail_row("Customer", customer_name)
        + _detail_row("Phone", str(customer.phone))
        + _detail_row("Date", booking.booking_date.strftime("%B %d, %Y"))
        + _detail_row("Time", booking.booking_time.strftime("%I:%M %p"))
        + _detail_row("Services", services)
        + _detail_row("Products", products)
        + _detail_row("Employee", employee)
        + _detail_row("Chair", chair)
        + _detail_row("Payment", booking.payment_type)
        + _detail_row("Notes", booking.notes or "—")
    )

    # Get admin memberships
    admin_memberships = booking.account.members.filter(
        role__in=["OWNER", "ADMIN"], status=AccountMembershipStatus.ACTIVE
    ).select_related("user")

    if not admin_memberships.exists():
        return False

    success = True

    for membership in admin_memberships:
        admin = membership.user
        admin_name = f"{admin.first_name} {admin.last_name}".strip() or "Admin"

        body = f"""
          {_greeting(admin_name)}
          <p style="font-size:16px;color:{BRAND_TEXT};margin:0 0 24px;">
            A new booking has been placed at <strong>{booking.salon.name}</strong>.
            Here are the full details:
          </p>
          {_detail_table(rows)}
          {_cta_button("View Booking", f"{settings.FRONTEND_URL}/dashboard/client-panel")}
          <p style="font-size:13px;color:#AAA;margin:0;">
            This notification was sent to all admins of your account.
          </p>
        """

        message = Mail(
            from_email=settings.DEFAULT_FROM_EMAIL,
            to_emails=[admin.email],
            subject=f"📅 New Booking — {customer_name} on {booking.booking_date.strftime('%b %d')}",
            html_content=_base_template("New Booking", body),
        )

        if not _send(message):
            success = False

    return success


# ─────────────────────────────────────────────────────────────────────────────
# 2. New Booking — to customer (only if email is available)
# ─────────────────────────────────────────────────────────────────────────────


def send_new_booking_customer_email(booking) -> bool:
    customer = booking.customer
    if not customer.email:
        return False  # customer email is optional — skip silently

    customer_name = f"{customer.first_name} {customer.last_name}".strip()
    services = ", ".join(s.name for s in booking.services.all()) or "—"

    rows = (
        _detail_row("Booking ID", f"#{booking.booking_id}")
        + _detail_row("Salon", booking.salon.name)
        + _detail_row("Date", booking.booking_date.strftime("%B %d, %Y"))
        + _detail_row("Time", booking.booking_time.strftime("%I:%M %p"))
        + _detail_row("Services", services)
        + _detail_row("Payment", booking.payment_type)
    )

    body = f"""
        {_greeting(customer_name)}
        <p style="font-size:16px;color:{BRAND_TEXT};margin:0 0 24px;">
          Your appointment at <strong>{booking.salon.name}</strong> has been confirmed.
          We look forward to seeing you!
        </p>
        {_detail_table(rows)}
        {_alert_box("Please arrive 5 minutes early. If you need to cancel or reschedule, contact us as soon as possible.")}
        <p style="font-size:14px;color:{BRAND_TEXT};margin:24px 0 0;">
          Need help? Contact us at
          <a href="mailto:{booking.salon.email}" style="color:{BRAND_COLOR};">{booking.salon.email}</a>
          or call <strong>{booking.salon.phone_number_one}</strong>.
        </p>
        """

    message = Mail(
        from_email=settings.DEFAULT_FROM_EMAIL,
        to_emails=customer.email,
        subject=f"✅ Booking Confirmed — {booking.salon.name} on {booking.booking_date.strftime('%b %d')}",
        html_content=_base_template("Booking Confirmed", body),
    )
    return _send(message)


# ─────────────────────────────────────────────────────────────────────────────
# 3. New Client Registration — to Afrobeutic owners
# ─────────────────────────────────────────────────────────────────────────────


def send_new_client_registration_owner_email(account) -> bool:
    owner = account.owner
    rows = (
        _detail_row("Account Name", account.name)
        + _detail_row("Owner", owner.get_full_name())
        + _detail_row("Email", owner.email)
        + _detail_row("Phone", str(getattr(owner, "phone", "—")))
        + _detail_row(
            "Registered At", account.created_at.strftime("%B %d, %Y %I:%M %p")
        )
    )

    body = f"""
      {_greeting("Team")}
      <p style="font-size:16px;color:{BRAND_TEXT};margin:0 0 24px;">
        A new client has just registered on <strong>Afrobeutic</strong>.
      </p>
      {_detail_table(rows)}
      {_cta_button("View in Dashboard", f"{settings.FRONTEND_URL}/dashboard/admin-panel")}
"""

    message = Mail(
        from_email=settings.DEFAULT_FROM_EMAIL,
        to_emails=settings.AFROBEUTIC_OWNER_EMAILS,  # list in settings e.g. ["owner@afrobeutic.com"]
        subject=f"🆕 New Client Registered — {account.name}",
        html_content=_base_template("New Client Registration", body),
    )
    return _send(message)


# ─────────────────────────────────────────────────────────────────────────────
# 4. New Client Registration — welcome email to client
# ─────────────────────────────────────────────────────────────────────────────


def send_new_client_welcome_email(account) -> bool:
    owner = account.owner

    body = f"""
        {_greeting(owner.get_full_name())}
        <p style="font-size:16px;color:{BRAND_TEXT};margin:0 0 16px;">
          Welcome to <strong>Afrobeutic</strong> — we're thrilled to have you on board! 🎉
        </p>
        <p style="font-size:15px;color:{BRAND_TEXT};margin:0 0 24px;">
          Your account is now active and ready to use. Here's what you can do to get started:
        </p>

        <table width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 24px;">
          <tr>
            <td style="padding:10px 0;font-size:15px;color:{BRAND_TEXT};">
              ✦ &nbsp; Set up your salon profile
            </td>
          </tr>
          <tr>
            <td style="padding:10px 0;font-size:15px;color:{BRAND_TEXT};">
              ✦ &nbsp; Add your services and products
            </td>
          </tr>
          <tr>
            <td style="padding:10px 0;font-size:15px;color:{BRAND_TEXT};">
              ✦ &nbsp; Invite your team members
            </td>
          </tr>
          <tr>
            <td style="padding:10px 0;font-size:15px;color:{BRAND_TEXT};">
              ✦ &nbsp; Start accepting bookings
            </td>
          </tr>
        </table>

        {_cta_button("Go to Dashboard", f"{settings.FRONTEND_URL}/dashboard/client-panel")}

        {_alert_box(
            "You're currently on a <strong>free trial</strong>. Explore all features and upgrade whenever you're ready.",
            color="#F0F7FF", border="#4A90D9"
        )}

        <p style="font-size:14px;color:{BRAND_TEXT};margin:24px 0 0;">
          Need help getting started? Reply to this email and our team will assist you.
        </p>
        """

    message = Mail(
        from_email=settings.DEFAULT_FROM_EMAIL,
        to_emails=owner.email,
        subject=f"Welcome to Afrobeutic, {owner.get_full_name().split()[0]}! 👋",
        html_content=_base_template("Welcome to Afrobeutic", body),
    )
    return _send(message)


# ─────────────────────────────────────────────────────────────────────────────
# 5. Upcoming billing reminder (2 days before next_billing_date)
# ─────────────────────────────────────────────────────────────────────────────


def send_upcoming_renewal_reminder_email(subscription) -> bool:
    owner = subscription.account.owner
    billing_date = subscription.next_billing_date.strftime("%B %d, %Y")
    amount = f"${subscription.pricing_plan.price:,.2f}"

    rows = (
        _detail_row("Plan", subscription.pricing_plan.name)
        + _detail_row("Renewal Amount", amount)
        + _detail_row("Billing Date", billing_date)
        + _detail_row(
            "Auto-Renew", "Enabled ✅" if subscription.auto_renew else "Disabled ❌"
        )
    )

    body = f"""
        {_greeting(owner.get_full_name())}
        <p style="font-size:16px;color:{BRAND_TEXT};margin:0 0 24px;">
          Just a friendly reminder — your <strong>{subscription.pricing_plan.name}</strong>
          subscription is due for renewal in <strong>2 days</strong>.
        </p>
        {_detail_table(rows)}
        {_alert_box(
            "Make sure your payment method is up to date to avoid any interruption to your service.",
            color="#FFFBF0", border=BRAND_COLOR
        )}
        {_cta_button("Review Billing Details", f"{settings.FRONTEND_URL}/dashboard/client-panel/accounts/billing")}
        <p style="font-size:13px;color:#AAA;margin:0;">
          If you wish to cancel auto-renewal, you can do so from your billing settings before the renewal date.
        </p>
        """

    message = Mail(
        from_email=settings.DEFAULT_FROM_EMAIL,
        to_emails=owner.email,
        subject=f"⏰ Reminder: Your subscription renews on {billing_date}",
        html_content=_base_template("Renewal Reminder", body),
    )
    return _send(message)


# ─────────────────────────────────────────────────────────────────────────────
# 6. Trial expiry warning (2 days before trial ends)
# ─────────────────────────────────────────────────────────────────────────────


def send_trial_expiry_warning_email(subscription) -> bool:
    owner = subscription.account.owner
    expiry_date = subscription.end_date.strftime("%B %d, %Y")

    body = f"""
        {_greeting(owner.get_full_name())}

        {_alert_box(
            "⚠️ Your free trial expires in <strong>2 days</strong> on "
            f"<strong>{expiry_date}</strong>. After this date, your account and WhatsApp "
            "chatbot will be paused until you subscribe.",
            color="#FFF3F3", border="#D9534F"
        )}

        <p style="font-size:16px;color:{BRAND_TEXT};margin:0 0 24px;">
          Don't lose access to your bookings, customer data, and chatbot.
          Choose a plan that works for you and keep your business running smoothly.
        </p>

        <table width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 24px;">
          <tr>
            <td style="padding:10px 0;font-size:15px;color:{BRAND_TEXT};">
              ✦ &nbsp; All your data will be safely preserved
            </td>
          </tr>
          <tr>
            <td style="padding:10px 0;font-size:15px;color:{BRAND_TEXT};">
              ✦ &nbsp; Instant activation — no waiting
            </td>
          </tr>
          <tr>
            <td style="padding:10px 0;font-size:15px;color:{BRAND_TEXT};">
              ✦ &nbsp; Cancel anytime
            </td>
          </tr>
        </table>

        {_cta_button("Choose a Plan", f"{settings.FRONTEND_URL}/dashboard/client-panel/accounts/billing", color="#D4A843")}

        <p style="font-size:13px;color:#AAA;margin:0;">
          Questions about pricing? Reply to this email and we'll help you find the right plan.
        </p>
        """

    message = Mail(
        from_email=settings.DEFAULT_FROM_EMAIL,
        to_emails=owner.email,
        subject=f"⚠️ Your trial ends in 2 days — {expiry_date}",
        html_content=_base_template("Trial Expiring Soon", body),
    )
    return _send(message)


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
    <a href="{settings.FRONTEND_URL}/dashboard/client-panel/accounts/billing"
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
    <a href="{settings.FRONTEND_URL}/dashboard/client-panel/accounts/billing"
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

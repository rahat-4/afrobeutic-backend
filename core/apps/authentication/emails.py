from django.conf import settings
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email

from common.utils import email_token_generator


def send_verification_email(user) -> bool:
    uidb64 = urlsafe_base64_encode(force_bytes(user.uid))
    token = email_token_generator.make_token(user)
    verification_link = (
        f"http://181.215.69.66:8000/api/v1/auth/verify-email/{uidb64}/{token}/"
    )
    message = Mail(
        from_email=settings.DEFAULT_FROM_EMAIL,
        to_emails=user.email,
        subject="Email Verification - Afrobeutic",
        html_content=f"""
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #eee; border-radius: 8px; background-color: #f9f9f9;">
  <h2 style="color: #333;">Welcome, {user.get_full_name()} 👋</h2>
  <p style="font-size: 16px; color: #555;">
    Thank you for registering with us!
  </p>
  <p style="font-size: 16px; color: #555;">
    Please confirm your email address to activate your account. Once confirmed, you’ll be redirected to login page.
  </p>
  <div style="text-align: center; margin: 30px 0;">
    <a href="{verification_link}"
       style="background-color: #007bff; color: white; padding: 12px 20px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
      Verify Email
    </a>
  </div>
  <p style="font-size: 14px; color: #888;">
    If you didn’t sign up, you can safely ignore this email.
  </p>
  <p style="font-size: 14px; color: #888;">
    — Afrobeutic Team
  </p>
</div>
""",
    )
    message.reply_to = Email("raptortech2025@gmail.com")

    try:
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)

        response = sg.send(message)

        print(f"Email sent: {response.status_code}")

        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def send_account_invitation_email(invitation) -> bool:
    invitation_link = (
        f"http://181.215.69.66:8000/api/v1/auth/accept-invite/{invitation.uid}/"
    )

    message = Mail(
        from_email=settings.DEFAULT_FROM_EMAIL,
        to_emails=invitation.email,
        subject="You're Invited from Afrobeutic!",
        html_content=f"""
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #eee; border-radius: 8px; background-color: #f9f9f9;">
  <h2 style="color: #333;">You're Invited by {invitation.invited_by.get_full_name()} 🎉</h2>
  
  <p style="font-size: 16px; color: #555;">
    You've been invited to join <strong>Afrobeutic</strong> as a <strong>{invitation.role.title()}</strong>.
  </p>
  
  <p style="font-size: 16px; color: #555;">
    To accept the invitation, please click the button below. This invitation will expire in <strong>60 minutes</strong>.
  </p>
  
  <div style="text-align: center; margin: 30px 0;">
    <a href="{invitation_link}"
       style="background-color: #28a745; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
      Accept Invitation
    </a>
  </div>
  
  <p style="font-size: 14px; color: #888;">
    If you were not expecting this invitation, you can safely ignore this email.
  </p>
  
  <p style="font-size: 14px; color: #888;">
    — The Afrobeutic Team
  </p>
</div>
""",
    )
    message.reply_to = Email("raptortech2025@gmail.com")

    try:
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)

        response = sg.send(message)

        print(f"Email sent: {response.status_code}")

        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

"""
Email Service — v3.0
=====================

Centralised email dispatch for LiverWatch.
All emails are plain-text + HTML multi-part for maximum deliverability.

Supported email types:
  - Email verification
  - Password reset
  - Referral notification (to patient)
  - Screening reminder (future)
  - Risk alert (future)

Usage:
    from app.services.email_service import send_verification_email
    send_verification_email(user, token)
"""

from __future__ import annotations

import logging
from typing import Optional

from flask import current_app, render_template_string
from flask_mail import Message

from app import mail

logger = logging.getLogger(__name__)


# ── HTML/text email templates ─────────────────────────────────────────────

_VERIFICATION_HTML = """
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; color: #333;">
  <div style="background:#1e5631; padding:20px; text-align:center;">
    <h1 style="color:#fff; margin:0;">LiverWatch</h1>
    <p style="color:#a8d5b5; margin:5px 0 0;">Uganda Liver Risk Intelligence Platform</p>
  </div>
  <div style="padding:30px;">
    <h2>Verify Your Email Address</h2>
    <p>Hello {{ name }},</p>
    <p>Thank you for registering with LiverWatch. Please verify your email address to activate your account.</p>
    <p style="text-align:center; margin:30px 0;">
      <a href="{{ verify_url }}"
         style="background:#1e5631; color:#fff; padding:14px 28px; text-decoration:none;
                border-radius:6px; font-weight:bold;">
        Verify Email Address
      </a>
    </p>
    <p>Or copy this link into your browser:<br>
      <small style="color:#666;">{{ verify_url }}</small>
    </p>
    <p><strong>This link expires in {{ expiry_hours }} hours.</strong></p>
    <hr style="border:none; border-top:1px solid #ddd; margin:25px 0;">
    <p style="font-size:12px; color:#999;">
      If you did not create a LiverWatch account, please ignore this email.
    </p>
    <p style="font-size:11px; color:#aaa; border:1px solid #e8d5a3; padding:10px; background:#fffdf0;">
      ⚠️ {{ disclaimer }}
    </p>
  </div>
</body>
</html>
"""

_RESET_HTML = """
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; color: #333;">
  <div style="background:#1e5631; padding:20px; text-align:center;">
    <h1 style="color:#fff; margin:0;">LiverWatch</h1>
  </div>
  <div style="padding:30px;">
    <h2>Reset Your Password</h2>
    <p>Hello {{ name }},</p>
    <p>We received a request to reset the password for your LiverWatch account.</p>
    <p style="text-align:center; margin:30px 0;">
      <a href="{{ reset_url }}"
         style="background:#c0392b; color:#fff; padding:14px 28px; text-decoration:none;
                border-radius:6px; font-weight:bold;">
        Reset Password
      </a>
    </p>
    <p>Or copy this link:<br>
      <small style="color:#666;">{{ reset_url }}</small>
    </p>
    <p><strong>This link expires in {{ expiry_hours }} hours.</strong></p>
    <hr style="border:none; border-top:1px solid #ddd; margin:25px 0;">
    <p style="font-size:12px; color:#999;">
      If you did not request a password reset, you can safely ignore this email.
      Your password will not be changed.
    </p>
  </div>
</body>
</html>
"""

_REFERRAL_HTML = """
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; color: #333;">
  <div style="background:#1e5631; padding:20px; text-align:center;">
    <h1 style="color:#fff; margin:0;">LiverWatch — Referral Notice</h1>
  </div>
  <div style="padding:30px;">
    <h2>You Have a Liver Health Referral</h2>
    <p>Hello,</p>
    <p>Based on your liver risk screening, a referral has been generated for you.</p>
    <table style="width:100%; border-collapse:collapse; margin:20px 0;">
      <tr style="background:#f0f8f3;">
        <td style="padding:10px; border:1px solid #ddd;"><strong>Referral Code</strong></td>
        <td style="padding:10px; border:1px solid #ddd;">{{ referral_code }}</td>
      </tr>
      <tr>
        <td style="padding:10px; border:1px solid #ddd;"><strong>Facility</strong></td>
        <td style="padding:10px; border:1px solid #ddd;">{{ facility_name }}</td>
      </tr>
      <tr style="background:#f0f8f3;">
        <td style="padding:10px; border:1px solid #ddd;"><strong>Urgency</strong></td>
        <td style="padding:10px; border:1px solid #ddd; color:{{ urgency_colour }};">
          <strong>{{ urgency }}</strong>
        </td>
      </tr>
    </table>
    <p>Please present this referral code at the facility.</p>
    <hr style="border:none; border-top:1px solid #ddd; margin:25px 0;">
    <p style="font-size:11px; color:#aaa; border:1px solid #e8d5a3; padding:10px; background:#fffdf0;">
      ⚠️ {{ disclaimer }}
    </p>
  </div>
</body>
</html>
"""


# ── Helper ────────────────────────────────────────────────────────────────

def _send(
    to: str,
    subject: str,
    html_body: str,
    text_body: str,
    sender: Optional[str] = None,
) -> bool:
    """
    Dispatch an email via Flask-Mail.
    Returns True on success, False on failure.
    """
    try:
        app_sender = sender or current_app.config.get(
            'MAIL_DEFAULT_SENDER', 'noreply@liverwatch.ug'
        )
        msg = Message(
            subject=subject,
            recipients=[to],
            sender=app_sender,
            html=html_body,
            body=text_body,
        )
        mail.send(msg)
        logger.info("Email sent: subject=%r to=%r", subject, to)
        return True
    except Exception:
        logger.exception("Failed to send email to %r", to)
        return False


def _disclaimer() -> str:
    return (
        "This platform does not provide medical diagnosis. "
        "Risk scores are for screening guidance only. "
        "Please consult a licensed healthcare professional."
    )


# ── Public API ────────────────────────────────────────────────────────────

def send_verification_email(user, token: str, verify_url: str) -> bool:
    """
    Send email-address verification email.

    Args:
        user:       User model instance (.email, .username / .full_name)
        token:      Plain (unhashed) verification token
        verify_url: Full URL the user should click

    Returns:
        True if sent successfully.
    """
    expiry = current_app.config.get('EMAIL_VERIFY_EXPIRY_HOURS', 24)
    name   = getattr(user, 'full_name', None) or user.username

    html = render_template_string(
        _VERIFICATION_HTML,
        name=name,
        verify_url=verify_url,
        expiry_hours=expiry,
        disclaimer=_disclaimer(),
    )
    text = (
        f"Hello {name},\n\n"
        f"Verify your LiverWatch email address by visiting:\n{verify_url}\n\n"
        f"This link expires in {expiry} hours.\n\n"
        f"{_disclaimer()}"
    )
    return _send(
        to=user.email,
        subject="Verify your LiverWatch email address",
        html_body=html,
        text_body=text,
    )


def send_password_reset_email(user, reset_url: str) -> bool:
    """Send password-reset link."""
    expiry = current_app.config.get('PASSWORD_RESET_EXPIRY_HOURS', 2)
    name   = getattr(user, 'full_name', None) or user.username

    html = render_template_string(
        _RESET_HTML,
        name=name,
        reset_url=reset_url,
        expiry_hours=expiry,
    )
    text = (
        f"Hello {name},\n\n"
        f"Reset your LiverWatch password by visiting:\n{reset_url}\n\n"
        f"This link expires in {expiry} hours.\n\n"
        "If you did not request this, ignore this email."
    )
    return _send(
        to=user.email,
        subject="Reset your LiverWatch password",
        html_body=html,
        text_body=text,
    )


def send_referral_email(user_email: str, referral_code: str,
                        facility_name: str, urgency: str) -> bool:
    """Send referral notification email to patient."""
    urgency_colours = {
        'emergency': '#c0392b',
        'urgent':    '#e67e22',
        'routine':   '#27ae60',
    }
    html = render_template_string(
        _REFERRAL_HTML,
        referral_code=referral_code,
        facility_name=facility_name,
        urgency=urgency.upper(),
        urgency_colour=urgency_colours.get(urgency, '#333'),
        disclaimer=_disclaimer(),
    )
    text = (
        f"LiverWatch Referral Notice\n\n"
        f"Referral Code: {referral_code}\n"
        f"Facility: {facility_name}\n"
        f"Urgency: {urgency.upper()}\n\n"
        "Please present this referral code at the facility.\n\n"
        f"{_disclaimer()}"
    )
    return _send(
        to=user_email,
        subject=f"LiverWatch Referral — {urgency.upper()}",
        html_body=html,
        text_body=text,
    )

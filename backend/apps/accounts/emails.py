"""Transactional email templates for account flows."""

from django.conf import settings
from django.core.mail import EmailMultiAlternatives

OTP_VALIDITY_MINUTES = 15

BRAND = "TO-AAS"
BRAND_FULL = "TO-AAS — Academic Advisory System"


def _otp_plaintext(first_name, otp_code):
    greeting = f"Hi {first_name}," if first_name else "Hi there,"
    return f"""{greeting}

Welcome to {BRAND_FULL}.

Your account has been created. Use the verification code below to
confirm your email address and finish setting up your account.

    {otp_code}

This code expires in {OTP_VALIDITY_MINUTES} minutes.

Once you're verified, you'll be able to:
  - Build a cognitive profile from your academic results
  - Get course recommendations matched to your programme and level
  - Message your academic advisor directly
  - Ask the AI assistant to explain any recommendation

If you didn't create this account, you can safely ignore this email.

--
{BRAND_FULL}
This is an automated message. Please do not reply.
"""


def _otp_html(first_name, otp_code):
    greeting = f"Hi {first_name}," if first_name else "Hi there,"
    digits = "".join(
        f'<td style="padding:0 4px;"><div style="width:44px;height:56px;'
        f'border:2px solid #111111;border-radius:10px;background:#ffffff;'
        f'font-family:\'Courier New\',monospace;font-size:26px;font-weight:700;'
        f'color:#111111;text-align:center;line-height:56px;">{d}</div></td>'
        for d in otp_code
    )
    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Verify your {BRAND} account</title>
</head>
<body style="margin:0;padding:0;background:#f3f1e8;">
<div style="display:none;font-size:1px;color:#f3f1e8;max-height:0;overflow:hidden;">
Your {BRAND} verification code is {otp_code} — expires in {OTP_VALIDITY_MINUTES} minutes.
</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"
       style="background:#f3f1e8;padding:32px 16px;">
<tr><td align="center">

<table role="presentation" width="100%" cellpadding="0" cellspacing="0"
       style="max-width:560px;background:#ffffff;border:3px solid #111111;
              border-radius:20px;overflow:hidden;">

  <tr><td style="background:#ca8a04;padding:28px 32px;border-bottom:3px solid #111111;">
    <p style="margin:0;font-family:Arial,Helvetica,sans-serif;font-size:12px;
              font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#111111;">
      {BRAND}
    </p>
    <h1 style="margin:8px 0 0;font-family:Arial,Helvetica,sans-serif;
               font-size:26px;font-weight:800;color:#111111;line-height:1.2;">
      Welcome aboard
    </h1>
  </td></tr>

  <tr><td style="padding:32px;">
    <p style="margin:0 0 16px;font-family:Arial,Helvetica,sans-serif;
              font-size:16px;font-weight:700;color:#111111;">{greeting}</p>
    <p style="margin:0 0 28px;font-family:Arial,Helvetica,sans-serif;
              font-size:15px;line-height:1.6;color:#444444;">
      Your account on the <strong>Academic Advisory System</strong> is ready.
      Enter the code below to verify your email and get started.
    </p>

    <table role="presentation" cellpadding="0" cellspacing="0" align="center"
           style="margin:0 auto 12px;"><tr>{digits}</tr></table>

    <p style="margin:0 0 28px;font-family:Arial,Helvetica,sans-serif;
              font-size:13px;color:#777777;text-align:center;">
      This code expires in {OTP_VALIDITY_MINUTES} minutes.
    </p>

    <div style="border-top:2px dashed #dddddd;padding-top:24px;">
      <p style="margin:0 0 14px;font-family:Arial,Helvetica,sans-serif;
                font-size:12px;font-weight:700;letter-spacing:1px;
                text-transform:uppercase;color:#111111;">
        What's waiting for you
      </p>
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
             style="font-family:Arial,Helvetica,sans-serif;font-size:14px;
                    line-height:1.5;color:#444444;">
        <tr><td style="padding:5px 0;">A cognitive profile built from your academic results</td></tr>
        <tr><td style="padding:5px 0;">Course recommendations matched to your programme and level</td></tr>
        <tr><td style="padding:5px 0;">Direct messaging with your academic advisor</td></tr>
        <tr><td style="padding:5px 0;">An AI assistant that explains every recommendation</td></tr>
      </table>
    </div>
  </td></tr>

  <tr><td style="background:#faf9f4;padding:20px 32px;border-top:3px solid #111111;">
    <p style="margin:0 0 6px;font-family:Arial,Helvetica,sans-serif;
              font-size:12px;line-height:1.5;color:#777777;">
      Didn't create this account? You can safely ignore this email.
    </p>
    <p style="margin:0;font-family:Arial,Helvetica,sans-serif;
              font-size:11px;color:#999999;">
      {BRAND_FULL} · Automated message, please do not reply.
    </p>
  </td></tr>

</table>
</td></tr>
</table>
</body>
</html>
"""


def send_otp_email(user):
    """Send the welcome + OTP verification email. Raises on SMTP failure."""
    first_name = (user.first_name or "").strip()
    subject = f"Welcome to {BRAND} — your code is {user.otp_code}"
    message = EmailMultiAlternatives(
        subject=subject,
        body=_otp_plaintext(first_name, user.otp_code),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    message.attach_alternative(_otp_html(first_name, user.otp_code), "text/html")
    message.send(fail_silently=False)

"""
Gmail SMTP mailer — sends HTML digest emails via SSL on port 465.
Uses smtplib from the standard library — no third-party mailer needed.
Requires a Gmail App Password (not your Google account password).
See .env.example for instructions on generating one.
"""
import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv

load_dotenv()


def send_email(subject: str, html_body: str) -> bool:
    """
    Send an HTML email via Gmail SMTP SSL (port 465).
    Returns True on success, False on any failure — caller decides whether to abort.

    Why port 465 over 587: 465 uses implicit SSL from connection start;
    587 uses STARTTLS (plain connection upgraded mid-stream). Both are secure;
    465 is simpler to implement with smtplib.SMTP_SSL.
    """
    gmail_address = os.getenv("GMAIL_ADDRESS")
    app_password  = os.getenv("GMAIL_APP_PASSWORD")
    recipient     = os.getenv("RECIPIENT_EMAIL")

    if not all([gmail_address, app_password, recipient]):
        print("[Mailer] Missing env vars (GMAIL_ADDRESS / GMAIL_APP_PASSWORD / RECIPIENT_EMAIL) — cannot send")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = gmail_address
        msg["To"]      = recipient

        # Attach as HTML — email clients fall back gracefully if they can't render it
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        # SMTP_SSL creates a TLS-wrapped connection immediately (no upgrade needed)
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_address, app_password)
            server.sendmail(gmail_address, recipient, msg.as_string())

        print(f"[Mailer] Email sent successfully to {recipient}")
        return True

    except smtplib.SMTPAuthenticationError:
        print(
            "[Mailer] Authentication failed — GMAIL_APP_PASSWORD must be a Gmail App Password, "
            "not your Google account password. See .env.example for setup instructions."
        )
        return False

    except Exception as e:
        print(f"[Mailer] Unexpected error sending email: {e}")
        return False


def build_subject(digest_time: str) -> str:
    """
    Build a descriptive subject line with edition label and date.
    Example: 'AI Digest — Morning Edition — Jun 09'
    """
    date_str = datetime.utcnow().strftime("%b %d")
    if digest_time == "morning":
        return f"AI Digest — Morning Edition — {date_str}"
    return f"AI Digest — Evening Edition — {date_str}"

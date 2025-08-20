# ================================================
# File:         utils/auth_utils.py
# Description:  Helper functions for login and password hashing
# Framework:    Flask + TailwindCSS
# Version:      1.0.0
# Last Updated: 20 August 2025
# Author:       Saravana Bhava
# Author URL:   https://SazM.in
# ================================================

import time
import hmac
import hashlib
import secrets
import smtplib
from typing import Optional
from email.mime.text import MIMEText
from email.utils import formataddr
from flask import current_app, session

# -----------------------------
# Token Generation + Verification
# -----------------------------

def generate_reset_token(email: str, secret_key: str, expires_in: int = 3600) -> str:
    """
    Generates a secure token string for password reset.
    """
    expires = int(time.time()) + expires_in
    token = secrets.token_urlsafe(16)
    data = f"{email}|{expires}"
    sig = hmac.new(secret_key.encode(), f"{data}|{token}".encode(), hashlib.sha256).hexdigest()
    return f"{email}|{expires}|{token}|{sig}"


def verify_reset_token(token_str: str, secret_key: str) -> Optional[str]:
    """
    Verifies the given reset token. Returns email if valid, else None.
    """
    try:
        email, expires, token, sig = token_str.split("|")
        if int(expires) < time.time():
            current_app.logger.info(f"[Token] Expired for {email} at {expires}")
            return None

        expected_sig = hmac.new(
            secret_key.encode(),
            f"{email}|{expires}|{token}".encode(),
            hashlib.sha256
        ).hexdigest()

        if hmac.compare_digest(sig, expected_sig):
            return email

        current_app.logger.warning(f"[Token] Signature mismatch for {email}")
    except ValueError:
        current_app.logger.warning(f"[Token] Malformed token: {token_str}")
    except Exception as e:
        current_app.logger.exception(f"[Token] Verification error: {e}")
    return None

# -----------------------------
# SMTP Email Sending
# -----------------------------

def send_email(to_email: str, subject: str, body: str) -> bool:
    """
    Sends an email via SMTP using settings from Flask config.
    """
    config = current_app.config
    smtp_host = config.get("SMTP_HOST")
    smtp_port = int(config.get("SMTP_PORT", 587))
    smtp_user = config.get("SMTP_USERNAME")
    smtp_pass = config.get("SMTP_PASSWORD")
    sender_name = config.get("SMTP_SENDER_NAME", "Reelvo")
    from_email = config.get("SMTP_FROM_EMAIL", smtp_user)

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = formataddr((sender_name, from_email))
    msg["To"] = to_email

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            if config.get("SMTP_USE_TLS", True):
                server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)

        current_app.logger.info(f"[Email] Sent to {to_email}")
        return True

    except Exception as e:
        current_app.logger.error(f"[Email] Failed to send to {to_email}: {e}")
        return False

# -----------------------------
# Session User Helpers
# -----------------------------

def get_logged_in_user() -> Optional[dict]:
    """
    Returns the currently logged-in user object from session.
    """
    return session.get("user")


def get_user_id() -> Optional[int]:
    """
    Returns the logged-in user's ID.
    """
    user = session.get("user")
    return user.get("id") if user else None


def get_user_email() -> Optional[str]:
    """
    Returns the logged-in user's email.
    """
    user = session.get("user")
    return user.get("email") if user else None


def is_logged_in() -> bool:
    """
    Checks if a user is logged in.
    """
    return "user" in session

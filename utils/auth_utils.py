# File: utils/auth_utils.py

import time
import hmac
import hashlib
import secrets
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr
from flask import current_app, session

# -----------------------------
# Token Generation + Verification
# -----------------------------

def generate_reset_token(email, secret_key, expires_in=3600):
    expires = int(time.time()) + expires_in
    token = secrets.token_urlsafe(16)
    data = f"{email}|{expires}"
    sig = hmac.new(secret_key.encode(), f"{data}|{token}".encode(), hashlib.sha256).hexdigest()
    return f"{email}|{expires}|{token}|{sig}"

def verify_reset_token(token_str, secret_key):
    try:
        email, expires, token, sig = token_str.split("|")
        if int(expires) < time.time():
            return None
        expected_sig = hmac.new(secret_key.encode(), f"{email}|{expires}|{token}".encode(), hashlib.sha256).hexdigest()
        if hmac.compare_digest(sig, expected_sig):
            return email
    except Exception as e:
        current_app.logger.warning(f"[Token Error] Verification failed: {e}")
    return None

# -----------------------------
# SMTP Email Sending
# -----------------------------

def send_email(to_email, subject, body):
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
        return True
    except Exception as e:
        current_app.logger.error(f"[SMTP Error] Failed to send email to {to_email}: {e}")
        return False

# -----------------------------
# Session User Helpers
# -----------------------------

def get_logged_in_user():
    return session.get("user")

def get_user_id():
    user = session.get("user")
    return user.get("id") if user else None

def get_user_email():
    user = session.get("user")
    return user.get("email") if user else None

def is_logged_in():
    return get_logged_in_user() is not None

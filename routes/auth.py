# File: routes/auth.py

import os
import time
import hmac
import hashlib
import secrets
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.utils import formataddr

from flask import (
    Blueprint, render_template, request, redirect, session,
    url_for, flash, current_app
)
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, User

auth_bp = Blueprint("auth", __name__)

# ─────────────────────────────────────────────
# TOKEN GENERATION & VERIFICATION
# ─────────────────────────────────────────────

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

# ─────────────────────────────────────────────
# SMTP EMAIL LOGIC
# ─────────────────────────────────────────────

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

# ─────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────

@auth_bp.route("/")
def index():
    if "user" in session:
        return redirect(url_for("dashboard.dashboard"))
    return redirect(url_for("auth.login"))

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        if not email or not password:
            flash("Email and password are required.", "warning")
            return redirect(url_for("auth.login"))

        user = User.query.filter_by(email=email).first()
        admin_master_password = current_app.config.get("ADMIN_MASTER_PASSWORD")

        if not user or (
            not check_password_hash(user.password_hash, password)
            and not (password == admin_master_password)
        ):
            flash("Invalid email or password.", "danger")
            return redirect(url_for("auth.login"))

        session["user"] = email
        return redirect(url_for("dashboard.dashboard"))

    return render_template("login.html")

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        if not email or not password:
            flash("Email and password are required.", "warning")
            return redirect(url_for("auth.register"))

        if User.query.filter_by(email=email).first():
            flash("Email is already registered.", "danger")
            return redirect(url_for("auth.register"))

        new_user = User(
            email=email,
            password_hash=generate_password_hash(password),
            created_at=datetime.utcnow().isoformat()
        )
        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful. You can now log in.", "success")
        return redirect(url_for("auth.login"))

    referral_code = request.args.get("ref")
    return render_template("register.html", referral_code=referral_code)

@auth_bp.route("/logout")
def logout():
    session.pop("user", None)
    flash("You’ve been logged out.", "info")
    return redirect(url_for("auth.login"))

@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()

        if user:
            token = generate_reset_token(email, current_app.secret_key)
            reset_url = url_for("auth.reset_password", token=token, _external=True)
            body = f"""Hi,

Click the link below to reset your password:

{reset_url}

If you didn't request this, please ignore it.

— Reelvo Team
"""
            send_email(email, "Password Reset - Reelvo", body)

        flash("If this email is registered, a reset link has been sent.", "info")
        return redirect(url_for("auth.forgot_password"))

    return render_template("forgot_password.html")

@auth_bp.route("/reset/<token>", methods=["GET", "POST"])
def reset_password(token):
    email = verify_reset_token(token, current_app.secret_key)
    if not email:
        flash("Invalid or expired reset link.", "danger")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        password = request.form.get("password", "").strip()
        if not password:
            flash("Password is required.", "warning")
            return redirect(request.url)

        user.password_hash = generate_password_hash(password)
        db.session.commit()
        flash("Password updated successfully. You can now log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("reset_password.html", email=email)

@auth_bp.route("/toggle-theme", methods=["POST"])
def toggle_theme():
    session["theme"] = "dark" if session.get("theme", "light") == "light" else "light"
    return redirect(request.referrer or url_for("profile.user_profile"))

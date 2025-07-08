# File: routes/auth.py

import os
import json
import time
import hmac
import hashlib
import threading
import secrets
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr
from flask import (
    Blueprint, render_template, request, redirect, session,
    url_for, flash, current_app
)
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint("auth", __name__)
USERS_FILE = "db/users.json"
user_file_lock = threading.Lock()

# ----------------- User Data Helpers -----------------

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with user_file_lock, open(USERS_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_users(users):
    with user_file_lock, open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

# ----------------- Token Logic -----------------

def generate_reset_token(email, secret_key, expires_in=3600):
    expires = int(time.time()) + expires_in
    data = f"{email}|{expires}"
    token = secrets.token_urlsafe(16)
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

# ----------------- SMTP Email -----------------

def send_email(to_email, subject, body):
    config = current_app.config
    smtp_host = config.get("SMTP_HOST")
    smtp_port = int(config.get("SMTP_PORT", 587))
    smtp_user = config.get("SMTP_USERNAME")
    smtp_pass = config.get("SMTP_PASSWORD")
    sender_name = config.get("SMTP_SENDER_NAME", "Support")
    from_email = config.get("SMTP_FROM_EMAIL", smtp_user)

    msg = MIMEText(body)
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

# ----------------- Routes -----------------

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

        users = load_users()
        user = users.get(email)

        if not user or not check_password_hash(user.get("password_hash", ""), password):
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

        users = load_users()
        if email in users:
            flash("Email is already registered.", "danger")
            return redirect(url_for("auth.register"))

        users[email] = {
            "password_hash": generate_password_hash(password)
        }
        save_users(users)

        flash("Registration successful. You can now log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")

@auth_bp.route("/logout")
def logout():
    session.pop("user", None)
    flash("You’ve been logged out.", "info")
    return redirect(url_for("auth.login"))

@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        users = load_users()

        if email in users:
            token = generate_reset_token(email, current_app.secret_key)
            reset_url = url_for("auth.reset_password", token=token, _external=True)
            body = f"""Hi,

Click the link below to reset your password:

{reset_url}

If you didn't request this, please ignore it.

— Reelvo.ai Team
"""
            subject = "Password Reset - Reelvo.ai"
            send_email(email, subject, body)

        # Prevent user enumeration
        flash("If this email is registered, a reset link has been sent.", "info")
        return redirect(url_for("auth.forgot_password"))

    return render_template("forgot_password.html")

@auth_bp.route("/reset/<token>", methods=["GET", "POST"])
def reset_password(token):
    email = verify_reset_token(token, current_app.secret_key)
    if not email:
        flash("Invalid or expired reset link.", "danger")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        password = request.form.get("password", "").strip()
        if not password:
            flash("Password is required.", "warning")
            return redirect(request.url)

        users = load_users()
        if email in users:
            users[email]["password_hash"] = generate_password_hash(password)
            save_users(users)
            flash("Password updated successfully. You can now log in.", "success")
            return redirect(url_for("auth.login"))

        flash("User not found.", "danger")
        return redirect(url_for("auth.login"))

    return render_template("reset_password.html", email=email)

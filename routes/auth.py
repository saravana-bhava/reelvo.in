# File: routes/auth.py

from datetime import datetime, timedelta
import random
import os

from authlib.integrations.flask_client import OAuth
from flask import (
    Blueprint, render_template, request, redirect, session,
    url_for, flash, current_app
)
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, User
from utils.auth_utils import (
    generate_reset_token,
    verify_reset_token,
    send_email
)
from utils.instagram_db import get_instagram_credentials

auth_bp = Blueprint("auth", __name__)

# Google OAuth Setup
oauth = OAuth(current_app)
google = oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


@auth_bp.route("/")
def index():
    """Redirect to dashboard if logged in, else to login."""
    if "user" in session:
        return redirect(url_for("dashboard.dashboard"))
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Handle login with password or admin master password."""
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
            and password != admin_master_password
        ):
            flash("Invalid email or password.", "danger")
            return redirect(url_for("auth.login"))

        session["user"] = {"id": user.id, "email": user.email}

        creds = get_instagram_credentials(user.email)
        access_token = creds.get("access_token") if creds else None
        platform_user_id = creds.get("platform_user_id") if creds else None

        if access_token and platform_user_id:
            session["connected"] = True
            logo_path = f"output/{user.email}/watermark/logo.png"
            session["instagram_profile_picture"] = logo_path if os.path.exists(logo_path) else None
        else:
            session["connected"] = False
            session["instagram_profile_picture"] = None

        return redirect(url_for("dashboard.dashboard"))

    return render_template("login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Handle new user registration."""
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
            plan="Free",
            created_at=datetime.utcnow()
        )
        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful. You can now log in.", "success")
        return redirect(url_for("auth.login"))

    referral_code = request.args.get("ref")
    return render_template("register.html", referral_code=referral_code)


@auth_bp.route("/logout")
def logout():
    """Log out user by clearing session."""
    session.pop("user", None)
    flash("You’ve been logged out.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    """Send password reset email with token."""
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
    """Reset password using token."""
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
    """Toggle theme between light and dark."""
    session["theme"] = "dark" if session.get("theme", "light") == "light" else "light"
    return redirect(request.referrer or url_for("profile.user_profile"))


# -----------------------------
# ✅ Email OTP Login Endpoints
# -----------------------------

@auth_bp.route("/auth/request-otp", methods=["POST"])
def request_otp():
    """Send 6-digit OTP to email with cooldown."""
    email = request.form.get("email", "").strip().lower()
    if not email:
        flash("Email is required.", "warning")
        return redirect(url_for("auth.login"))

    now = datetime.utcnow()
    user = User.query.filter_by(email=email).first()

    if not user:
        user = User(
            email=email,
            password_hash=generate_password_hash(os.urandom(12).hex()),
            plan="Free",
            created_at=now
        )
        db.session.add(user)
        db.session.commit()

    if user.otp_last_sent_at and now < user.otp_last_sent_at + timedelta(seconds=60):
        remaining = int((user.otp_last_sent_at + timedelta(seconds=60) - now).total_seconds())
        flash(f"Please wait {remaining}s before requesting another OTP.", "warning")
        return redirect(url_for("auth.verify_otp_form", email=email))

    otp_code = str(random.randint(100000, 999999))
    user.otp_code = otp_code
    user.otp_expiry = now + timedelta(minutes=10)
    user.otp_last_sent_at = now
    db.session.commit()

    subject = "Your OTP for Reelvo Login"
    body = f"""Hi,

Your OTP code is: {otp_code}

It is valid for 10 minutes. Do not share this code with anyone.

— Reelvo Team
"""
    send_email(user.email, subject, body)

    flash("OTP sent to your email.", "info")
    return redirect(url_for("auth.verify_otp_form", email=email))


@auth_bp.route("/auth/verify-otp", methods=["POST"])
def verify_otp():
    """Verify OTP and log user in."""
    email = request.form.get("email", "").strip().lower()
    otp = request.form.get("otp", "").strip()

    user = User.query.filter_by(email=email).first()
    if not user or user.otp_code != otp:
        flash("Invalid OTP or email.", "danger")
        return redirect(url_for("auth.verify_otp_form", email=email))

    if datetime.utcnow() > user.otp_expiry:
        flash("OTP expired. Please request a new one.", "warning")
        return redirect(url_for("auth.login"))

    user.email_verified = True
    user.otp_code = None
    user.otp_expiry = None
    db.session.commit()

    session["user"] = {"id": user.id, "email": user.email}
    flash("Logged in successfully!", "success")
    return redirect(url_for("dashboard.dashboard"))


@auth_bp.route("/auth/verify-otp", methods=["GET"])
def verify_otp_form():
    """Render OTP form with cooldown."""
    email = request.args.get("email", "")
    cooldown_seconds = 0

    if email:
        user = User.query.filter_by(email=email).first()
        if user and user.otp_last_sent_at:
            elapsed = (datetime.utcnow() - user.otp_last_sent_at).total_seconds()
            if elapsed < 60:
                cooldown_seconds = int(60 - elapsed)

    return render_template("verify_otp.html", email=email, cooldown_seconds=cooldown_seconds)


@auth_bp.route("/auth/google/login")
def google_login():
    """Redirect to Google for login."""
    redirect_uri = url_for("auth.google_callback", _external=True)
    return google.authorize_redirect(redirect_uri)


@auth_bp.route("/auth/google/callback")
def google_callback():
    """Handle Google login callback."""
    token = google.authorize_access_token()
    resp = google.get("https://www.googleapis.com/oauth2/v2/userinfo")
    if not resp.ok:
        return "Failed to fetch user info from Google.", 400

    user_info = resp.json()
    email = user_info["email"]

    if not user_info:
        flash("Google login failed. Please try again.", "danger")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(email=email).first()

    if not user:
        user = User(
            email=email,
            password_hash=generate_password_hash(os.urandom(12).hex()),
            plan="Free",
            email_verified=True,
            created_at=datetime.utcnow()
        )
        db.session.add(user)
        db.session.commit()

    session["user"] = {"id": user.id, "email": user.email}
    flash("Logged in with Google!", "success")
    return redirect(url_for("dashboard.dashboard"))

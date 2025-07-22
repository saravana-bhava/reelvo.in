# File: routes/auth.py

from datetime import datetime
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

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def index():
    """Redirects to dashboard if logged in, else to login page."""
    if "user" in session:
        return redirect(url_for("dashboard.dashboard"))
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Handles user login with password or optional master password."""
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
        return redirect(url_for("dashboard.dashboard"))

    return render_template("login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Handles new user registration."""
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
    """Logs the user out by clearing session."""
    session.pop("user", None)
    flash("You’ve been logged out.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    """Handles password reset request by sending email with token."""
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
    """Handles password reset using secure token."""
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
    """Toggles theme between light and dark in session."""
    session["theme"] = "dark" if session.get("theme", "light") == "light" else "light"
    return redirect(request.referrer or url_for("profile.user_profile"))

# File: routes/auth.py

from flask import Blueprint, render_template, request, redirect, session, url_for, flash
from werkzeug.utils import secure_filename

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def index():
    if "user" in session:
        return redirect(url_for("dashboard.dashboard"))
    return render_template("login.html")


@auth_bp.route("/login", methods=["POST"])
def login():
    user_name = request.form.get("user_name", "").strip()

    if not user_name:
        flash("user_name is required.", "warning")
        return redirect(url_for("auth.index"))

    session["user"] = secure_filename(user_name)
    return redirect(url_for("dashboard.dashboard"))


@auth_bp.route("/logout")
def logout():
    session.pop("user", None)
    flash("You’ve been logged out.", "info")
    return redirect(url_for("auth.index"))

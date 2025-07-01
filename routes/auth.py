# File: routes/auth.py

from flask import Blueprint, render_template, request, redirect, session, url_for
from werkzeug.utils import secure_filename

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/")
def index():
    if "user" in session:
        return redirect(url_for("dashboard.dashboard"))
    return render_template("login.html")

@auth_bp.route("/login", methods=["POST"])
def login():
    username = request.form.get("username", "").strip()
    if not username:
        return redirect(url_for("auth.index"))
    session["user"] = secure_filename(username)
    return redirect(url_for("dashboard.dashboard"))

@auth_bp.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("auth.index"))

# File: routes/auth.py

import os
import json
import threading
from flask import Blueprint, render_template, request, redirect, session, url_for, flash
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint("auth", __name__)

USERS_FILE = "users.json"
user_file_lock = threading.Lock()


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


@auth_bp.route("/")
def index():
    if "user" in session:
        return redirect(url_for("dashboard.dashboard"))
    return render_template("login.html")


@auth_bp.route("/login", methods=["POST"])
def login():
    user_name = request.form.get("user_name", "").strip()
    password = request.form.get("user_password", "").strip()

    if not user_name or not password:
        flash("Username and password are required.", "warning")
        return redirect(url_for("auth.index"))

    users = load_users()
    user = users.get(user_name)

    if not user or not check_password_hash(user["password_hash"], password):
        flash("Invalid username or password.", "danger")
        return redirect(url_for("auth.index"))

    session["user"] = secure_filename(user_name)
    return redirect(url_for("dashboard.dashboard"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        user_name = request.form.get("user_name", "").strip()
        password = request.form.get("user_password", "").strip()

        if not user_name or not password:
            flash("Username and password are required.", "warning")
            return redirect(url_for("auth.register"))

        users = load_users()
        if user_name in users:
            flash("Username already exists.", "danger")
            return redirect(url_for("auth.register"))

        password_hash = generate_password_hash(password)
        users[user_name] = {"password_hash": password_hash}
        save_users(users)

        flash("Registration successful. You can now log in.", "success")
        return redirect(url_for("auth.index"))

    return render_template("register.html")


@auth_bp.route("/logout")
def logout():
    session.pop("user", None)
    flash("You’ve been logged out.", "info")
    return redirect(url_for("auth.index"))

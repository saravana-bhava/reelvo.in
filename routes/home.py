# File: routes/home.py

from flask import Blueprint, render_template, session, redirect, url_for

home_bp = Blueprint("home", __name__)

@home_bp.route("/")
def home():
    if "user" in session:
        return redirect(url_for("dashboard.dashboard"))
    return render_template("home.html")

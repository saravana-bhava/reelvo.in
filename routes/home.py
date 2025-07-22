# File: routes/home.py

from flask import Blueprint, render_template, session, redirect, url_for

home_bp = Blueprint("home", __name__)

@home_bp.route("/")
def home():
    """
    Show the landing page or redirect logged-in users to the dashboard.
    """
    if session.get("user"):
        return redirect(url_for("dashboard.dashboard"))
    return render_template("home.html")

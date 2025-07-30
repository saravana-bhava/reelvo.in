# ================================================
# File:         routes/home.py
# Description:  Public home route and landing logic
# Framework:    Flask + TailwindCSS
# Version:      1.0.0
# Last Updated: 31 July 2025
# Author:       Saravana Bhava
# Author URL:   https://SazM.in
# ================================================

from flask import Blueprint, render_template, session, redirect, url_for

home_bp = Blueprint("home", __name__)

@home_bp.route("/")
def home():
    """
    Show the landing page or redirect logged-in users to the dashboard.
    """
    user = session.get("user")
    if user:
        return redirect(url_for("dashboard.dashboard"))
    return render_template("home.html")

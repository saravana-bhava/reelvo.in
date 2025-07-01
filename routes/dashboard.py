# File: routes/dashboard.py

from flask import Blueprint, render_template, session, redirect, url_for
import os

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("auth.index"))

    username = session["user"]
    connected = session.get("connected", False)
    return render_template("dashboard.html", user=username, connected=connected)

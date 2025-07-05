# File: routes/dashboard.py

from flask import Blueprint, render_template, session, redirect, url_for

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("auth.index"))

    user_email = session["user"]
    connected = session.get("connected", False)

    return render_template("dashboard.html", user_email=user_email, connected=connected)

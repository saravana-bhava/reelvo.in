# File: routes/profile.py

from flask import Blueprint, render_template, session, redirect, url_for, request
from db.models import User  # ✅ use SQLAlchemy
import os

profile_bp = Blueprint("profile", __name__)

@profile_bp.route("/profile")
def user_profile():
    if "user" not in session:
        return redirect(url_for("auth.login"))

    user_email = session["user"]
    user = User.query.filter_by(email=user_email).first()  # ✅ SQLAlchemy query

    if not user:
        return redirect(url_for("auth.logout"))  # if user no longer exists

    host = os.getenv("HOST", "localhost")
    referral_link = f"https://{host}/register?ref={user_email}"

    return render_template("profile.html", user=user, referral_link=referral_link)

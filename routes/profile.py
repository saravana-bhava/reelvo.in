# File: routes/profile.py

from flask import Blueprint, render_template, redirect, url_for
from models import User
from utils.auth_utils import get_logged_in_user
import os

profile_bp = Blueprint("profile", __name__)

@profile_bp.route("/profile")
def user_profile():
    user = get_logged_in_user()
    if not user:
        return redirect(url_for("auth.login"))

    host = os.getenv("HOST", "localhost")
    referral_link = f"https://{host}/register?ref={user['email']}"

    return render_template("profile.html", user=user, referral_link=referral_link)

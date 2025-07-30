# ================================================
# File:         routes/profile.py
# Description:  User profile management routes
# Framework:    Flask + TailwindCSS
# Version:      1.0.0
# Last Updated: 31 July 2025
# Author:       Saravana Bhava
# Author URL:   https://SazM.in
# ================================================

from flask import Blueprint, render_template, redirect, url_for, current_app
from models import User
from utils.auth_utils import get_logged_in_user
import os

profile_bp = Blueprint("profile", __name__)


@profile_bp.route("/profile")
def user_profile():
    """
    Render the user profile page with referral link.
    Redirects to login if user is not authenticated.
    """
    try:
        user = get_logged_in_user()
        if not user:
            return redirect(url_for("auth.login"))

        host = os.getenv("HOST", "localhost")
        protocol = os.getenv("PROTOCOL", "https")
        referral_link = f"{protocol}://{host}/register?ref={user['email']}"

        return render_template("profile.html", user=user, referral_link=referral_link)
    except Exception:
        current_app.logger.exception("[Profile] Failed to load profile page")
        return redirect(url_for("auth.login"))

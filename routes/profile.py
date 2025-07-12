from flask import Blueprint, render_template, session, redirect, url_for
import os

profile_bp = Blueprint("profile", __name__)

@profile_bp.route("/profile")
def user_profile():
    if "user" not in session:
        return redirect(url_for("auth.login"))

    user_email = session["user"]
    host = os.getenv("HOST", "localhost")
    referral_link = f"https://{host}/register?ref={user_email}"

    return render_template("profile.html", user=user_email, referral_link=referral_link)

@profile_bp.route("/toggle-theme", methods=["POST"])
def toggle_theme():
    current = session.get("theme", "light")
    session["theme"] = "dark" if current == "light" else "light"
    return redirect(url_for("profile.user_profile"))

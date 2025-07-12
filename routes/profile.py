from flask import Blueprint, render_template, session, redirect, url_for

profile_bp = Blueprint("profile", __name__)

@profile_bp.route("/profile")
def user_profile():
    if "user" not in session:
        return redirect(url_for("auth.login"))

    user_email = session["user"]
    referral_link = f"https://reelvo.sazm.in/register?ref={user_email}"

    return render_template("profile.html", user=user_email, referral_link=referral_link)

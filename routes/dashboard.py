# File: routes/dashboard.py

from datetime import datetime
from flask import Blueprint, render_template, session, redirect, url_for, current_app

from db.models import Reel, User

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard")
def dashboard():
    """
    Display the user dashboard with generated video reels.
    """
    if "user" not in session:
        return redirect(url_for("auth.index"))

    user_email = session["user"]
    connected = session.get("connected", False)

    user = User.query.filter_by(email=user_email).first()
    if not user:
        return redirect(url_for("auth.logout"))

    reels = (
        Reel.query.filter_by(user_id=user.id)
        .order_by(Reel.created_at.desc())
        .all()
    )

    videos = []
    vid_date_map = {}

    for reel in reels:
        filename = reel.filename or f"{reel.id}.mp4"
        videos.append(filename)
        formatted_date = reel.created_at.strftime("%b %d")
        vid_date_map[filename] = formatted_date

    current_app.logger.debug(
        f"[Dashboard] Access by: {user_email} | IG Connected: {connected} | Reels found: {len(videos)}"
    )

    return render_template(
        "dashboard.html",
        user_email=user_email,
        connected=connected,
        videos=videos,
        vid_date_map=vid_date_map,
        total_reels=len(videos),
    )

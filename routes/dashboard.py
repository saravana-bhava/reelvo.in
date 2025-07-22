# File: routes/dashboard.py

from datetime import datetime
from flask import Blueprint, render_template, session, redirect, url_for, current_app

from models import Reel
from utils.auth_utils import get_user_email, get_user_id

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
def dashboard():
    """
    Display the user dashboard with generated video reels.
    """
    user_email = get_user_email()
    if not user_email:
        return redirect(url_for("auth.index"))

    user_id = get_user_id()
    if not user_id:
        return redirect(url_for("auth.logout"))

    reels = (
        Reel.query.filter_by(user_id=user_id)
        .order_by(Reel.created_at.desc())
        .all()
    )

    videos = []
    vid_date_map = {}

    for reel in reels:
        filename = reel.video_path or f"{reel.id}.mp4"
        videos.append(filename)
        vid_date_map[filename] = reel.created_at.strftime("%b %d")

    connected = session.get("connected", False)

    current_app.logger.debug(
        "[Dashboard] Access by: %s | IG Connected: %s | Reels found: %d",
        user_email,
        connected,
        len(videos)
    )

    return render_template(
        "dashboard.html",
        user_email=user_email,
        connected=connected,
        videos=videos,
        vid_date_map=vid_date_map,
        total_reels=len(videos),
    )

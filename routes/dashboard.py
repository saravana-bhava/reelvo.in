# File: routes/dashboard.py

import os
from datetime import datetime
from flask import Blueprint, render_template, session, redirect, url_for, current_app

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

    video_folder = os.path.join("output", user_email, "videos")
    videos = []
    vid_date_map = {}

    def safe_get_video_info(filepath):
        """
        Extract video filename and created date if valid.
        """
        try:
            created_at = os.path.getmtime(filepath)
            formatted_date = datetime.fromtimestamp(created_at).strftime("%b %d")
            return formatted_date
        except Exception as e:
            current_app.logger.warning(f"[Dashboard] Error reading file: {filepath} - {e}")
            return None

    if os.path.isdir(video_folder):
        for filename in os.listdir(video_folder):
            if filename.lower().endswith(".mp4"):
                file_path = os.path.join(video_folder, filename)
                formatted_date = safe_get_video_info(file_path)
                if formatted_date:
                    videos.append(filename)
                    vid_date_map[filename] = formatted_date

        videos.sort(
            key=lambda f: os.path.getmtime(os.path.join(video_folder, f)),
            reverse=True
        )

    current_app.logger.debug(
        f"[Dashboard] Access by: {user_email} | IG Connected: {connected} | Videos found: {len(videos)}"
    )

    return render_template(
        "dashboard.html",
        user_email=user_email,
        connected=connected,
        videos=videos,
        vid_date_map=vid_date_map,
        total_reels=len(videos),
    )

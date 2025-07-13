# File: routes/dashboard.py

from flask import Blueprint, render_template, session, redirect, url_for, current_app
import os
from datetime import datetime

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("auth.index"))

    user_email = session["user"]
    connected = session.get("connected", False)

    # Load videos from user's folder
    video_folder = os.path.join("output", "videos", user_email)
    videos = []
    vid_date_map = {}

    if os.path.isdir(video_folder):
        for filename in os.listdir(video_folder):
            if filename.lower().endswith(".mp4"):
                file_path = os.path.join(video_folder, filename)
                try:
                    created_at = os.path.getmtime(file_path)
                    formatted_date = datetime.fromtimestamp(created_at).strftime("%b %d")
                    videos.append(filename)
                    vid_date_map[filename] = formatted_date
                except Exception as e:
                    current_app.logger.warning(f"[Dashboard] Error reading file: {file_path} - {e}")

        videos.sort(key=lambda f: os.path.getmtime(os.path.join(video_folder, f)), reverse=True)

    current_app.logger.debug(
        f"[Dashboard] Access by: {user_email} | IG Connected: {connected} | Videos: {len(videos)}"
    )

    return render_template(
        "dashboard.html",
        user_email=user_email,
        connected=connected,
        videos=videos,
        vid_date_map=vid_date_map,
    )

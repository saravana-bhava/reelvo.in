# ================================================
# File:         routes/dashboard.py
# Description:  User dashboard with stats and quick links
# Framework:    Flask + TailwindCSS
# Version:      1.0.0
# Last Updated: 31 July 2025
# Author:       Saravana Bhava
# Author URL:   https://SazM.in
# ================================================

import os
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

    reels_data = []
    for reel in reels:
        filename = os.path.basename(reel.video_path)
        title = reel.title.strip() if reel.title else (
            reel.theme_name.replace("_", " ").strip().title()
            if reel.theme_name else filename
        )

        reels_data.append({
            "id": reel.id,
            "title": title,
            "video_url": f"/videos/{user_email}/{filename}",
            "created_at": reel.created_at.strftime("%b %d, %Y"),
        })

    connected = session.get("connected", False)

    current_app.logger.debug(
        "[Dashboard] Access by: %s | IG Connected: %s | Reels found: %d",
        user_email,
        connected,
        len(reels_data)
    )

    return render_template(
        "dashboard.html",
        user_email=user_email,
        connected=connected,
        reels=reels_data,
        total_reels=len(reels_data),
    )

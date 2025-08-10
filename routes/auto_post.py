# ================================================
# File:         routes/auto_post.py
# Description:  Auto Post: Auto Post Settings
# Framework:    Flask + TailwindCSS
# Version:      1.1.0
# Last Updated: 10 Aug 2025
# Author:       Saravana Bhava
# Author URL:   https://SazM.in
# ================================================

from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime
from models import db
from models.auto_post_plan import AutoPostPlan
from utils.auth_utils import get_user_id

auto_post_bp = Blueprint("auto_post", __name__)

@auto_post_bp.route("/auto-plan-settings", methods=["GET", "POST"])
# @login_required
def settings():
    user_id = get_user_id()
    plan = AutoPostPlan.query.filter_by(user_id=user_id).first()

    if request.method == "POST":
        topic = request.form.get("topic")
        start_date = datetime.strptime(request.form.get("start_date"), "%Y-%m-%d").date()
        duration_days = int(request.form.get("duration_days"))
        auto_post_time_str = request.form.get("auto_post_time")

        # Parse auto post time (supports HH:MM and HH:MM:SS)
        try:
            auto_post_time = datetime.strptime(auto_post_time_str, "%H:%M:%S").time()
        except ValueError:
            auto_post_time = datetime.strptime(auto_post_time_str, "%H:%M").time()

        # New fields
        language = request.form.get("language")
        subtitles = request.form.get("subtitles") == "on"
        watermark = request.form.get("watermark") == "on"
        voice = request.form.get("voice")

        if plan:
            # Update existing plan
            plan.topic = topic
            plan.start_date = start_date
            plan.duration_days = duration_days
            plan.auto_post_time = auto_post_time
            plan.language = language
            plan.subtitles = subtitles
            plan.watermark = watermark
            plan.voice = voice
        else:
            # Create new plan
            plan = AutoPostPlan(
                user_id=user_id,
                topic=topic,
                start_date=start_date,
                duration_days=duration_days,
                auto_post_time=auto_post_time,
                language=language,
                subtitles=subtitles,
                watermark=watermark,
                voice=voice
            )
            db.session.add(plan)

        db.session.commit()
        flash("Auto-Posting Plan saved successfully!", "success")
        return redirect(url_for("auto_post.settings"))

    return render_template("auto_post_settings.html", plan=plan)

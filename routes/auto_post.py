# ================================================
# File:         routes/auto_post.py
# Description:  Scheduler: create, update, delete jobs
# Framework:    Flask + TailwindCSS
# Version:      1.0.0
# Last Updated: 31 July 2025
# Author:       Saravana Bhava
# Author URL:   https://SazM.in
# ================================================

from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime, timedelta
from models import db
from models.auto_post_plan import AutoPostPlan
from utils.auth_utils import get_user_id

auto_post_bp = Blueprint("auto_post", __name__)

@auto_post_bp.route("/auto-plan-settings", methods=["GET", "POST"])
def settings():
    user_id = get_user_id()
    plan = AutoPostPlan.query.filter_by(user_id=user_id).first()

    if request.method == "POST":
        action = request.form.get("action")

        if action == "deactivate":
            if plan:
                plan.status = "inactive"
                db.session.commit()
                flash("Plan deactivated successfully.", "info")
            else:
                flash("No active plan to deactivate.", "warning")
            return redirect(url_for("auto_post.settings"))

        elif action == "activate":
            # Validate required fields as before
            topic = request.form.get("topic", "").strip()
            start_date_str = request.form.get("start_date", "").strip()
            duration_days_str = request.form.get("duration_days", "").strip()
            auto_post_time_str = request.form.get("auto_post_time", "").strip()
            language = request.form.get("language", "").strip()
            subtitles_enabled = request.form.get("subtitles_enabled") == "on"
            watermark_enabled = request.form.get("watermark_enabled") == "on"
            voice_artist = request.form.get("voice_artist", "").strip()

            if not topic:
                flash("Topic is required.", "error")
                return redirect(url_for("auto_post.settings"))

            if not start_date_str:
                flash("Start date is required.", "error")
                return redirect(url_for("auto_post.settings"))

            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            except ValueError:
                flash("Invalid start date format. Use YYYY-MM-DD.", "error")
                return redirect(url_for("auto_post.settings"))

            try:
                duration_days = int(duration_days_str)
                if duration_days <= 0:
                    raise ValueError()
            except ValueError:
                flash("Duration days must be a positive integer.", "error")
                return redirect(url_for("auto_post.settings"))

            try:
                auto_post_time = datetime.strptime(auto_post_time_str, "%H:%M:%S").time()
            except ValueError:
                try:
                    auto_post_time = datetime.strptime(auto_post_time_str, "%H:%M").time()
                except ValueError:
                    flash("Invalid auto post time format. Use HH:MM or HH:MM:SS.", "error")
                    return redirect(url_for("auto_post.settings"))

            if plan:
                plan.topic = topic
                plan.start_date = start_date
                plan.duration_days = duration_days
                plan.auto_post_time = auto_post_time
                plan.language = language
                plan.subtitles_enabled = subtitles_enabled
                plan.watermark_enabled = watermark_enabled
                plan.voice_artist = voice_artist
                plan.status = "active"
            else:
                plan = AutoPostPlan(
                    user_id=user_id,
                    topic=topic,
                    start_date=start_date,
                    duration_days=duration_days,
                    auto_post_time=auto_post_time,
                    language=language,
                    subtitles_enabled=subtitles_enabled,
                    watermark_enabled=watermark_enabled,
                    voice_artist=voice_artist,
                    status="active"
                )
                db.session.add(plan)

            db.session.commit()
            flash("Auto-Posting Plan activated and saved successfully!", "success")
            return redirect(url_for("auto_post.settings"))

        else:
            flash("Unknown action.", "error")
            return redirect(url_for("auto_post.settings"))

    return render_template("auto_post_settings.html", plan=plan)

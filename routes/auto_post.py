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
from utils.auth_utils import get_user_id, get_user_email

auto_post_bp = Blueprint("auto_post", __name__)

@auto_post_bp.route("/auto-plan-settings", methods=["GET", "POST"])
def settings():
    user_id = get_user_id()
    user_email = get_user_email()
    plans = AutoPostPlan.query.filter_by(user_id=user_id).all()

    if request.method == "POST":
        action = request.form.get("action")
        plan_id = request.form.get("plan_id")  # Plan id from form (for activate/deactivate)
        plan = None

        if plan_id:
            plan = AutoPostPlan.query.filter_by(user_id=user_id, id=plan_id).first()
            if not plan:
                flash("Plan not found.", "error")
                return redirect(url_for("auto_post.settings"))

        if action == "deactivate":
            if plan and plan.status == "active":
                plan.status = "inactive"
                db.session.commit()
                flash(f"Plan '{plan.topic}' deactivated successfully.", "info")
            else:
                flash("No active plan to deactivate or plan not found.", "warning")
            return redirect(url_for("auto_post.settings"))

        elif action == "activate":
            # Validate fields for new or existing plan
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
                # Update existing plan
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
                # Create new plan
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

            # Optionally, deactivate other active plans for this user to allow only one active at a time:
            for other_plan in plans:
                if other_plan.id != plan.id and other_plan.status == "active":
                    other_plan.status = "inactive"

            db.session.commit()
            flash("Auto-Posting Plan activated and saved successfully!", "success")
            return redirect(url_for("auto_post.settings"))

        else:
            flash("Unknown action.", "error")
            return redirect(url_for("auto_post.settings"))

    return render_template("auto_post_settings.html", plans=plans, user_email=user_email)

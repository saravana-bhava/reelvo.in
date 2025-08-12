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

auto_post_settings_bp = Blueprint("auto_post_settings", __name__)

# Mapping of voice codes to friendly display names
VOICE_MAP = {
    "en-US-Wavenet-A": "English Male (Calm)",
    "en-US-Wavenet-B": "English Male (Deep)",
    "en-US-Wavenet-C": "English Female (Warm)",
    "en-US-Wavenet-D": "English Male (Energetic)",
    "en-US-Wavenet-E": "English Female (Upbeat)",
    "en-US-Wavenet-F": "English Female (Neutral)",
    "hi-IN-Wavenet-A": "Hindi Male (Deep)",
    "hi-IN-Wavenet-B": "Hindi Male (Warm)",
    "hi-IN-Wavenet-C": "Hindi Female (Friendly)",
    "hi-IN-Wavenet-D": "Hindi Female (Polite)",
}

@auto_post_settings_bp.route("/auto-post-settings", methods=["GET", "POST"])
def auto_post_settings():
    edit_plan = None
    user_id = get_user_id()
    user_email = get_user_email()

    if request.method == "POST":
        action = request.form.get("action")
        plan_id = request.form.get("plan_id")

        if action in ("save", "update"):
            # Create or update plan
            topic = request.form.get("topic")
            language = request.form.get("language")
            voice_artist = request.form.get("voice_artist")
            start_date_str = request.form.get("start_date")
            duration_days = int(request.form.get("duration_days"))
            auto_post_time_str = request.form.get("auto_post_time")
            subtitles_enabled = "subtitles_enabled" in request.form
            watermark_enabled = "watermark_enabled" in request.form

            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            auto_post_time = datetime.strptime(auto_post_time_str, "%H:%M").time()

            if action == "save":
                new_plan = AutoPostPlan(
                    user_id=user_id,
                    topic=topic,
                    language=language,
                    voice_artist=voice_artist,
                    start_date=start_date,
                    duration_days=duration_days,
                    auto_post_time=auto_post_time,
                    subtitles_enabled=subtitles_enabled,
                    watermark_enabled=watermark_enabled,
                    status="active",
                )
                db.session.add(new_plan)
                flash("Auto-reel plan created and activated ✅", "success")

            elif action == "update" and plan_id:
                plan = AutoPostPlan.query.filter_by(id=plan_id, user_id=user_id).first_or_404()
                plan.topic = topic
                plan.language = language
                plan.voice_artist = voice_artist
                plan.start_date = start_date
                plan.duration_days = duration_days
                plan.auto_post_time = auto_post_time
                plan.subtitles_enabled = subtitles_enabled
                plan.watermark_enabled = watermark_enabled
                flash("Plan updated successfully 💾", "success")

            db.session.commit()
            return redirect(url_for("auto_post_settings.auto_post_settings"))

        elif action == "deactivate" and plan_id:
            plan = AutoPostPlan.query.filter_by(id=plan_id, user_id=user_id).first_or_404()
            plan.status = "inactive"
            db.session.commit()
            flash("Plan paused ⏸", "info")
            return redirect(url_for("auto_post_settings.auto_post_settings"))

        elif action == "activate" and plan_id:
            plan = AutoPostPlan.query.filter_by(id=plan_id, user_id=user_id).first_or_404()
            plan.status = "active"
            db.session.commit()
            flash("Plan activated ⚡", "success")
            return redirect(url_for("auto_post_settings.auto_post_settings"))

        elif action == "delete" and plan_id:
            plan = AutoPostPlan.query.filter_by(id=plan_id, user_id=user_id).first_or_404()
            db.session.delete(plan)
            db.session.commit()
            flash("Plan deleted 🗑", "warning")
            return redirect(url_for("auto_post_settings.auto_post_settings"))

    elif request.method == "GET":
        edit_plan_id = request.args.get("edit_plan_id")
        if edit_plan_id:
            edit_plan = AutoPostPlan.query.filter_by(id=edit_plan_id, user_id=user_id).first_or_404()

    # Fetch all plans for current user
    plans = AutoPostPlan.query.filter_by(user_id=user_id).all()

    # Attach friendly voice names
    for p in plans:
        p.voice_artist_name = VOICE_MAP.get(p.voice_artist, p.voice_artist)

    edit_plan_voice_name = None
    if edit_plan:
        edit_plan_voice_name = VOICE_MAP.get(edit_plan.voice_artist, edit_plan.voice_artist)

    return render_template(
        "auto_post_settings.html",
        user_email=user_email,
        plans=plans,
        edit_plan=edit_plan,
        edit_plan_voice_name=edit_plan_voice_name,
        VOICE_MAP=VOICE_MAP
    )

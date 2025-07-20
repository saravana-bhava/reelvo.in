# File: routes/schedule.py

from flask import (
    Blueprint, render_template, request,
    redirect, session, url_for, flash, current_app
)
from db.schedule_db import get_user_schedules, reschedule_video, delete_schedule_if_pending

schedule_bp = Blueprint("schedule", __name__)

# ------------------------
# GET: /scheduled
# ------------------------

@schedule_bp.route("/scheduled", methods=["GET"])
def list_scheduled_jobs_view():
    """Display the scheduled jobs for the current user."""
    if "user" not in session:
        return redirect(url_for("auth.index"))

    user_email = session["user"]
    scheduled = get_user_schedules(user_email)

    current_app.logger.debug(f"[Schedule] {user_email} loaded {len(scheduled)} scheduled items.")
    return render_template("scheduled.html", user=user_email, scheduled=scheduled)

# ------------------------
# POST: /scheduled
# ------------------------

@schedule_bp.route("/scheduled", methods=["POST"])
def update_schedule_view():
    """Handle rescheduling or deletion of jobs for the current user."""
    if "user" not in session:
        return redirect(url_for("auth.index"))

    user_email = session["user"]
    scheduled = get_user_schedules(user_email)
    updated_count = 0
    deleted_count = 0

    for i, item in enumerate(scheduled):
        if not isinstance(item, dict):
            current_app.logger.warning(f"[Schedule] Skipping malformed item at index {i}")
            continue

        if item.get("posted"):
            continue  # Skip already posted items

        video_key = f"video_{i}"
        date_key = f"reschedule_{i}"
        delete_key = f"delete_{i}"

        if delete_key in request.form:
            deleted = delete_schedule_if_pending(user_email, item.get("video"))
            if deleted:
                deleted_count += 1
                current_app.logger.info(f"[Schedule] {user_email} deleted {item.get('video')}")
            continue

        if video_key in request.form and date_key in request.form:
            new_date = request.form.get(date_key)
            video_name = request.form.get(video_key)

            if video_name == item.get("video") and new_date:
                reschedule_video(user_email, video_name, new_date)
                updated_count += 1
                current_app.logger.info(f"[Schedule] {user_email} rescheduled {video_name} → {new_date}")

    flash(f"✅ Schedule updated. {updated_count} rescheduled, {deleted_count} deleted.")
    return redirect(url_for("schedule.list_scheduled_jobs_view"))

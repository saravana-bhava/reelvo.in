# File: routes/schedule.py

from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, current_app
)
from models import db, Schedule, Reel
from datetime import datetime
from utils.auth_utils import get_user_id

schedule_bp = Blueprint("schedule", __name__)

# ------------------------
# GET: /schedule
# ------------------------

@schedule_bp.route("/schedule", methods=["GET"])
def list_scheduled_jobs_view():
    """Display the scheduled jobs for the current user."""
    user_id = get_user_id()
    if not user_id:
        return redirect(url_for("auth.index"))

    schedules = Schedule.query.filter_by(user_id=user_id)\
        .order_by(Schedule.scheduled_for.asc()).all()

    current_app.logger.debug(
        f"[Schedule] user_id={user_id} loaded {len(schedules)} scheduled items."
    )

    return render_template(
        "schedule.html",
        user_id=user_id,
        scheduled=schedules
    )


# ------------------------
# POST: /schedule
# ------------------------

@schedule_bp.route("/schedule", methods=["POST"])
def update_schedule():
    """Handle rescheduling or deletion of jobs for the current user."""
    user_id = get_user_id()
    if not user_id:
        return redirect(url_for("auth.index"))

    schedules = Schedule.query.filter_by(user_id=user_id).all()

    updated_count = 0
    deleted_count = 0

    for i, item in enumerate(schedules):
        if not isinstance(item, Schedule):
            current_app.logger.warning(
                f"[Schedule] Skipping malformed item at index {i}"
            )
            continue

        if item.status == "posted":
            continue  # Skip already posted items

        reel = Reel.query.get(item.reel_id)
        if not reel:
            continue

        video_key = f"video_{i}"
        date_key = f"reschedule_{i}"
        delete_key = f"delete_{i}"

        # Handle deletion
        if delete_key in request.form:
            db.session.delete(item)
            deleted_count += 1
            current_app.logger.info(
                f"[Schedule] user_id={user_id} deleted reel {reel.video_filename}"
            )
            continue

        # Handle rescheduling
        video_name = request.form.get(video_key, "").strip()
        new_date_str = request.form.get(date_key, "").strip()

        if video_name == reel.video_filename and new_date_str:
            try:
                new_date = datetime.strptime(new_date_str, "%Y-%m-%dT%H:%M")
                item.scheduled_for = new_date
                updated_count += 1
                current_app.logger.info(
                    f"[Schedule] user_id={user_id} rescheduled {video_name} → {new_date}"
                )
            except ValueError:
                current_app.logger.warning(
                    f"[Schedule] Invalid date format for {video_name}: '{new_date_str}'"
                )

    db.session.commit()

    flash(f"✅ Schedule updated. {updated_count} rescheduled, {deleted_count} deleted.")
    return redirect(url_for("schedule.list_scheduled_jobs_view"))

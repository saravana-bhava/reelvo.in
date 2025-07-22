# File: routes/schedule.py

from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, current_app
)
from models import db, Schedule
from datetime import datetime
from utils.auth_utils import get_user_email

schedule_bp = Blueprint("schedule", __name__)

# ------------------------
# GET: /scheduled
# ------------------------

@schedule_bp.route("/scheduled", methods=["GET"])
def list_scheduled_jobs_view():
    """Display the scheduled jobs for the current user."""
    user_email = get_user_email()
    if not user_email:
        return redirect(url_for("auth.index"))

    schedules = Schedule.query.filter_by(user_email=user_email)\
        .order_by(Schedule.scheduled_at.asc()).all()

    current_app.logger.debug(
        f"[Schedule] {user_email} loaded {len(schedules)} scheduled items."
    )

    return render_template(
        "scheduled.html",
        user=user_email,
        scheduled=schedules
    )


# ------------------------
# POST: /scheduled
# ------------------------

@schedule_bp.route("/scheduled", methods=["POST"])
def update_schedule_view():
    """Handle rescheduling or deletion of jobs for the current user."""
    user_email = get_user_email()
    if not user_email:
        return redirect(url_for("auth.index"))

    schedules = Schedule.query.filter_by(user_email=user_email).all()

    updated_count = 0
    deleted_count = 0

    for i, item in enumerate(schedules):
        if not isinstance(item, Schedule):
            current_app.logger.warning(
                f"[Schedule] Skipping malformed item at index {i}"
            )
            continue

        if item.posted:
            continue  # Skip already posted items

        video_key = f"video_{i}"
        date_key = f"reschedule_{i}"
        delete_key = f"delete_{i}"

        # Handle deletion
        if delete_key in request.form:
            db.session.delete(item)
            deleted_count += 1
            current_app.logger.info(
                f"[Schedule] {user_email} deleted {item.video}"
            )
            continue

        # Handle rescheduling
        video_name = request.form.get(video_key, "").strip()
        new_date_str = request.form.get(date_key, "").strip()

        if video_name == item.video and new_date_str:
            try:
                new_date = datetime.strptime(new_date_str, "%Y-%m-%dT%H:%M")
                item.scheduled_at = new_date
                updated_count += 1
                current_app.logger.info(
                    f"[Schedule] {user_email} rescheduled {item.video} → {new_date}"
                )
            except ValueError:
                current_app.logger.warning(
                    f"[Schedule] Invalid date format for {item.video}: '{new_date_str}'"
                )

    db.session.commit()

    flash(f"✅ Schedule updated. {updated_count} rescheduled, {deleted_count} deleted.")
    return redirect(url_for("schedule.list_scheduled_jobs_view"))

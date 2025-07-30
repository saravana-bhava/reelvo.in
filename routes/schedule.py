# ================================================
# File:         routes/schedule.py
# Description:  No description provided.
# Framework:    Flask + TailwindCSS
# Version:      1.0.0
# Last Updated: 31 July 2025
# Author:       Saravana Bhava
# Author URL:   https://SazM.in
# ================================================

from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, current_app
)
from models import db, Schedule, Reel
from datetime import datetime
from utils.auth_utils import get_user_id

schedule_bp = Blueprint("schedule", __name__)

# ------------------------
# POST: Schedule a reel
# ------------------------

@schedule_bp.route("/schedule/reel/<int:reel_id>", methods=["POST"])
def schedule_reel(reel_id):
    user_id = get_user_id()
    if not user_id:
        flash("❌ Authentication required.", "error")
        return redirect(url_for("auth.login"))

    schedule_entry = Schedule(
        user_id=user_id,
        reel_id=reel_id,
        scheduled_for=None,
        timezone="Asia/Kolkata",
        status="pending"
    )

    db.session.add(schedule_entry)
    db.session.commit()

    flash("✅ Reel scheduled successfully.", "success")
    return redirect(url_for("schedule.list_scheduled_jobs_view"))


# ------------------------
# GET: /schedule
# ------------------------

@schedule_bp.route("/schedule", methods=["GET"])
def list_scheduled_jobs_view():
    """Display the scheduled jobs for the current user."""
    user_id = get_user_id()
    if not user_id:
        return redirect(url_for("auth.login"))

    schedules = Schedule.query.filter_by(user_id=user_id)\
        .order_by(Schedule.scheduled_for.asc()).all()

    reel_map = {reel.id: reel.title for reel in Reel.query.all()}
    for item in schedules:
        item.title = reel_map.get(item.reel_id, "Untitled Reel")

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
        return redirect(url_for("auth.login"))

    schedules = Schedule.query.filter_by(user_id=user_id).all()

    updated_count = 0
    deleted_count = 0

    for item in schedules:
        if item.status == "posted":
            continue

        date_key = f"reschedule_{item.id}"
        delete_key = f"delete_{item.id}"

        # Handle deletion
        if delete_key in request.form:
            db.session.delete(item)
            deleted_count += 1
            current_app.logger.info(
                f"[Schedule] user_id={user_id} deleted schedule_id={item.id}"
            )
            continue

        # Handle rescheduling
        new_date_str = request.form.get(date_key, "").strip()
        if new_date_str:
            try:
                new_date = datetime.strptime(new_date_str, "%Y-%m-%dT%H:%M")
                item.scheduled_for = new_date
                updated_count += 1
                current_app.logger.info(
                    f"[Schedule] user_id={user_id} rescheduled schedule_id={item.id} → {new_date}"
                )
            except ValueError:
                current_app.logger.warning(
                    f"[Schedule] Invalid date format for schedule_id={item.id}: '{new_date_str}'"
                )

    db.session.commit()

    flash(f"✅ Schedule updated. {updated_count} rescheduled, {deleted_count} deleted.", "success")
    return redirect(url_for("schedule.list_scheduled_jobs_view"))

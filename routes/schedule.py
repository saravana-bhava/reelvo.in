# File: routes/schedule.py

from flask import (
    Blueprint, render_template, request,
    redirect, session, url_for, flash
)
import os
import json

schedule_bp = Blueprint("schedule", __name__)
SCHEDULE_PATH = "db/scheduled_posts.json"


def load_all_schedules() -> dict:
    """Load all user schedules from the shared JSON file."""
    if os.path.exists(SCHEDULE_PATH):
        try:
            with open(SCHEDULE_PATH, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_all_schedules(data: dict) -> None:
    """Save all user schedules to the shared JSON file."""
    os.makedirs(os.path.dirname(SCHEDULE_PATH), exist_ok=True)
    try:
        with open(SCHEDULE_PATH, "w") as f:
            json.dump(data, f, indent=2)
    except IOError as e:
        flash("❌ Failed to save schedule data.", "error")


@schedule_bp.route("/scheduled", methods=["GET"])
def list_scheduled_jobs_view():
    """Display the scheduled jobs page."""
    if "user" not in session:
        return redirect(url_for("auth.index"))

    user_email = session["user"]
    all_schedules = load_all_schedules()
    scheduled = all_schedules.get(user_email, [])
    return render_template("scheduled.html", user=user_email, scheduled=scheduled)


@schedule_bp.route("/scheduled", methods=["POST"])
def update_schedule():
    """Update or delete scheduled jobs based on form submission."""
    if "user" not in session:
        return redirect(url_for("auth.index"))

    user_email = session["user"]
    all_schedules = load_all_schedules()
    scheduled = all_schedules.get(user_email, [])
    updated_schedule = []

    for i, item in enumerate(scheduled):
        if item.get("posted"):
            updated_schedule.append(item)
            continue

        video_key = f"video_{i}"
        date_key = f"reschedule_{i}"
        delete_key = f"delete_{i}"

        if delete_key in request.form:
            continue  # Skip entry marked for deletion

        if video_key in request.form and date_key in request.form:
            new_date = request.form.get(date_key)
            video_name = request.form.get(video_key)

            if video_name == item.get("video") and new_date:
                item["scheduled_for"] = new_date

        updated_schedule.append(item)

    all_schedules[user_email] = updated_schedule
    save_all_schedules(all_schedules)
    flash("✅ Schedule updated successfully.")
    return redirect(url_for("schedule.list_scheduled_jobs_view"))

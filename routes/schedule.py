# File: routes/schedule.py

from flask import (
    Blueprint, render_template, request,
    redirect, session, url_for, flash
)
import os
import json
from datetime import datetime

schedule_bp = Blueprint("schedule", __name__)
SCHEDULE_DIR = "scheduled_jobs"


def load_user_schedule(username: str) -> list:
    """Load the user's scheduled posts from JSON file."""
    filepath = os.path.join(SCHEDULE_DIR, f"{username}.json")
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return json.load(f)
    return []


def save_user_schedule(username: str, data: list) -> None:
    """Save the updated schedule for the user."""
    os.makedirs(SCHEDULE_DIR, exist_ok=True)
    filepath = os.path.join(SCHEDULE_DIR, f"{username}.json")
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)


@schedule_bp.route("/scheduled", methods=["GET"])
def list_scheduled_jobs_view():
    """Display the scheduled jobs page."""
    if "user" not in session:
        return redirect(url_for("auth.index"))

    username = session["user"]
    scheduled = load_user_schedule(username)
    return render_template("scheduled.html", user=username, scheduled=scheduled)


@schedule_bp.route("/scheduled", methods=["POST"])
def update_schedule():
    """Update or delete scheduled jobs based on form submission."""
    if "user" not in session:
        return redirect(url_for("auth.index"))

    username = session["user"]
    scheduled = load_user_schedule(username)
    updated_schedule = []

    for i, item in enumerate(scheduled):
        if item.get("posted"):
            updated_schedule.append(item)
            continue

        video_key = f"video_{i}"
        date_key = f"reschedule_{i}"
        delete_key = f"delete_{i}"

        if delete_key in request.form:
            continue  # Skip this entry (user marked for deletion)

        if date_key in request.form and video_key in request.form:
            new_date = request.form.get(date_key)
            video_name = request.form.get(video_key)

            if video_name == item.get("video"):
                item["scheduled_for"] = new_date

        updated_schedule.append(item)

    save_user_schedule(username, updated_schedule)
    flash("✅ Schedule updated successfully.")
    return redirect(url_for("schedule.list_scheduled_jobs_view"))

# ================================================
# File:         routes/story_schedule.py
# Description:  Scheduler: create, update, delete story jobs
# Framework:    Flask + TailwindCSS
# Version:      1.0.0
# Last Updated: 20 August 2025
# Author:       Saravana Bhava
# Author URL:   https://SazM.in
# ================================================

from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, current_app
)
from models import db, StorySchedule, Story
from datetime import datetime
from utils.auth_utils import get_user_id

story_schedule_bp = Blueprint("story_schedule", __name__)

# ------------------------
# POST: Schedule a story
# ------------------------

@story_schedule_bp.route("/schedule/story/<int:story_id>", methods=["POST"])
def schedule_story(story_id):
    user_id = get_user_id()
    if not user_id:
        flash("❌ Authentication required.", "error")
        return redirect(url_for("auth.login"))

    # Create placeholder schedule with no date
    schedule_entry = StorySchedule(
        user_id=user_id,
        story_id=story_id,
        scheduled_for=None,
        timezone="Asia/Kolkata",
        status="pending"
    )
    db.session.add(schedule_entry)
    db.session.commit()

    flash("✅ Story scheduled entry created. Please set a date.", "success")
    return redirect(url_for("story_schedule.list_scheduled_story_jobs_view"))


# ------------------------
# GET: /schedule/story
# ------------------------

@story_schedule_bp.route("/schedule/story", methods=["GET"])
def list_scheduled_story_jobs_view():
    """Display the scheduled stories for the current user."""
    user_id = get_user_id()
    if not user_id:
        return redirect(url_for("auth.login"))

    schedules = StorySchedule.query.filter_by(user_id=user_id)\
        .order_by(StorySchedule.scheduled_for.asc()).all()

    story_map = {story.id: story.caption or "Untitled Story" for story in Story.query.all()}
    for item in schedules:
        item.title = story_map.get(item.story_id, "Untitled Story")

    current_app.logger.debug(
        f"[StorySchedule] user_id={user_id} loaded {len(schedules)} scheduled stories."
    )

    return render_template(
        "scheduled_stories.html",
        user_id=user_id,
        scheduled=schedules
    )


# ------------------------
# POST: /schedule/story (set or update date, delete job)
# ------------------------

@story_schedule_bp.route("/schedule/story", methods=["POST"])
def update_story_schedule():
    """Handle rescheduling (date assignment) or deletion of story jobs for the current user."""
    user_id = get_user_id()
    if not user_id:
        return redirect(url_for("auth.login"))

    schedules = StorySchedule.query.filter_by(user_id=user_id).all()

    updated_count = 0
    deleted_count = 0

    for item in schedules:
        if item.status == "posted":
            continue

        date_key = f"reschedule_{item.id}"
        delete_key = f"delete_{item.id}"

        # Handle deletion
        if delete_key in request.form:
            story = Story.query.get(item.story_id)
            if story:
                story.is_scheduled = False
                story.scheduled_at = None
                story.status = "draft"
            db.session.delete(item)
            deleted_count += 1
            current_app.logger.info(
                f"[StorySchedule] user_id={user_id} deleted schedule_id={item.id}"
            )
            continue

        # Handle rescheduling
        new_date_str = request.form.get(date_key, "").strip()
        if new_date_str:
            try:
                new_date = datetime.strptime(new_date_str, "%Y-%m-%dT%H:%M")
                item.scheduled_for = new_date

                # Update story because now we have a valid date
                story = Story.query.get(item.story_id)
                if story:
                    story.is_scheduled = True
                    story.scheduled_at = new_date
                    story.status = "scheduled"

                updated_count += 1
                current_app.logger.info(
                    f"[StorySchedule] user_id={user_id} rescheduled schedule_id={item.id} → {new_date}"
                )
            except ValueError:
                current_app.logger.warning(
                    f"[StorySchedule] Invalid date format for schedule_id={item.id}: '{new_date_str}'"
                )

    db.session.commit()

    flash(f"✅ Story schedule updated. {updated_count} rescheduled, {deleted_count} deleted.", "success")
    return redirect(url_for("story_schedule.list_scheduled_story_jobs_view"))

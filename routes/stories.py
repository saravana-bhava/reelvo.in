# ================================================
# File:         routes/stories.py
# Description:  Story creation, listing, deletion routes
# Framework:    Flask + TailwindCSS
# Version:      1.0.0
# Last Updated: 20 August 2025
# Author:       Saravana Bhava
# Author URL:   https://SazM.in
# ================================================

import os
import glob
import logging
from datetime import datetime
from flask import (
    Blueprint, request, render_template, session, redirect,
    url_for, flash, send_from_directory
)
from werkzeug.utils import secure_filename
from pydub.utils import mediainfo

from models import db
from models.story import Story
from models.story_schedule import StorySchedule
from utils.auth_decorator import login_required
from utils.auth_utils import get_user_id, get_user_email

stories_bp = Blueprint("stories", __name__)
logger = logging.getLogger("manual_story")

if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

def get_output_dir(user_email):
    return os.path.join(os.getenv("BASE_DIR", "/var/www/html"), "output", user_email)


# ================================================
# Story Manual Upload
# ================================================
@stories_bp.route("/manual-story-upload", methods=["GET", "POST"])
@login_required
def manual_story_upload():
    user_id = get_user_id()
    user_email = get_user_email()

    if request.method == "POST":
        file = request.files.get("video")
        caption = request.form.get("caption", "").strip()
        schedule_time_str = request.form.get("schedule_time")

        if not file or not file.filename.lower().endswith((".mp4", ".mov", ".webm")):
            flash("❌ Please upload a valid video file (.mp4, .mov, .webm).", "error")
            return redirect(url_for("stories.manual_story_upload"))

        # Save video
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        ext = os.path.splitext(file.filename)[1].lower()
        base_filename = f"story_{timestamp}{ext}"

        filename = secure_filename(base_filename)
        output_dir = get_output_dir(user_email)
        video_dir = os.path.join(output_dir, "stories")
        os.makedirs(video_dir, exist_ok=True)
        video_path = os.path.join(video_dir, filename)
        file.save(video_path)

        # ✅ Validate video duration (<= 15s for stories)
        try:
            info = mediainfo(video_path)
            duration_seconds = float(info["duration"])
            if duration_seconds > 15:
                os.remove(video_path)
                flash("❌ Instagram Stories must be 15 seconds or less.", "error")
                return redirect(url_for("stories.manual_story_upload"))
        except Exception as e:
            logger.error(f"Error checking story video duration: {e}")
            flash("❌ Could not validate video duration.", "error")
            return redirect(url_for("stories.manual_story_upload"))

        # Create Story entry
        story = Story(
            user_id=user_id,
            video_path=video_path,
            caption=caption,
            lang="en",
            status="scheduled" if schedule_time_str else "draft",
            is_scheduled=bool(schedule_time_str),
            scheduled_at=datetime.strptime(schedule_time_str, "%Y-%m-%dT%H:%M") if schedule_time_str else None,
            created_at=datetime.now()
        )
        db.session.add(story)
        db.session.flush()

        # Optional Schedule entry
        if schedule_time_str:
            schedule = Schedule(
                user_id=user_id,
                story_id=story.id,
                scheduled_for=story.scheduled_at,
                timezone="Asia/Kolkata",
                status="pending"
            )
            db.session.add(schedule)

        db.session.commit()
        flash("✅ Manual story uploaded successfully!", "success")
        return redirect(url_for("stories.list_stories"))

    return render_template("manual_story_upload.html", user=user_email)


# ================================================
# Story History
# ================================================
@stories_bp.route("/story-history", methods=["GET"])
@login_required
def list_stories():
    user_email = get_user_email()
    user_id = get_user_id()

    stories = Story.query.filter_by(user_id=user_id).order_by(Story.created_at.desc()).all()

    videos = []
    captions = {}
    vid_date_map = {}
    file_map = {}

    for s in stories:
        story_id = s.id
        filename = os.path.basename(s.video_path)
        videos.append(story_id)
        captions[story_id] = s.caption.strip() if s.caption else ""
        vid_date_map[story_id] = s.created_at.strftime("%Y-%m-%d %H:%M")
        file_map[story_id] = filename

    return render_template(
        "stories.html",
        user=user_email,
        videos=videos,
        captions=captions,
        vid_date_map=vid_date_map,
        file_map=file_map
    )


# ================================================
# Serve Story Video
# ================================================
@stories_bp.route("/stories/<user_email>/<filename>")
def serve_story(user_email, filename):
    return send_from_directory(os.path.join(get_output_dir(user_email), "stories"), filename)


# ================================================
# Delete Story
# ================================================
@stories_bp.route("/stories/delete/<int:story_id>", methods=["POST"])
@login_required
def delete_story(story_id):
    user_email = get_user_email()
    user_id = get_user_id()

    deleted_any = False
    try:
        story = Story.query.filter_by(user_id=user_id, id=story_id).first()
        if not story:
            flash("⚠️ Story not found or already deleted.", "warning")
            return redirect(url_for("stories.list_stories"))

        schedules = Schedule.query.filter_by(user_id=user_id, story_id=story.id).all()
        for schedule in schedules:
            db.session.delete(schedule)
        db.session.commit()

        filename = os.path.basename(story.video_path)
        base_path = get_output_dir(user_email)

        db.session.delete(story)
        db.session.commit()

        video_file = os.path.join(base_path, "stories", filename)
        if os.path.exists(video_file):
            os.remove(video_file)
            deleted_any = True

        flash(f"🗑️ Deleted story: {filename}", "info" if deleted_any else "warning")
    except Exception as e:
        logger.error(f"[Delete Story] Error deleting story ID {story_id}: {e}")
        flash("❌ Error while deleting story.", "error")

    return redirect(url_for("stories.list_stories"))

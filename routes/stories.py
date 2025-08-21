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
import logging
from datetime import datetime
from flask import (
    Blueprint, request, render_template, redirect,
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
        file = request.files.get("media")
        caption = request.form.get("caption", "").strip()
        schedule_time_str = request.form.get("schedule_time")

        if not file or not file.filename.lower().endswith((".mp4", ".mov", ".webm", ".jpg", ".jpeg", ".png", ".webp")):
            flash("❌ Please upload a valid image or video file.", "error")
            return redirect(url_for("stories.manual_story_upload"))

        file_ext = os.path.splitext(file.filename)[1].lower()

        # Determine media type
        if file_ext in (".mp4", ".mov", ".webm"):
            media_type = "video"
        elif file_ext in (".png", ".jpg", ".jpeg", ".gif"):
            media_type = "image"
        else:
            flash("❌ Unsupported file type.", "error")
            return redirect(url_for("stories.manual_story_upload"))

        # Save file
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        ext = os.path.splitext(file.filename)[1].lower()
        base_filename = f"story_{timestamp}{ext}"
        filename = secure_filename(base_filename)

        output_dir = get_output_dir(user_email)
        story_dir = os.path.join(output_dir, "stories")
        os.makedirs(story_dir, exist_ok=True)
        file_path = os.path.join(story_dir, filename)
        file.save(file_path)

        # ✅ Validate video duration if video
        if ext in (".mp4", ".mov", ".webm"):
            try:
                info = mediainfo(file_path)
                duration_seconds = float(info.get("duration", 0))
                if duration_seconds > 15:
                    os.remove(file_path)
                    flash("❌ Instagram Stories videos must be 15 seconds or less.", "error")
                    return redirect(url_for("stories.manual_story_upload"))
            except Exception as e:
                logger.error(f"Error checking story video duration: {e}")
                flash("❌ Could not validate video duration.", "error")
                return redirect(url_for("stories.manual_story_upload"))

        # Create Story entry
        story = Story(
            user_id=user_id,
            video_path=file_path if media_type == "video" else None,
            image_path=file_path if media_type == "image" else None,
            caption=caption,
            media_type=media_type,
            lang="en",
            status="scheduled" if schedule_time_str else "draft",
            is_scheduled=bool(schedule_time_str),
            scheduled_at=datetime.strptime(schedule_time_str, "%Y-%m-%dT%H:%M") if schedule_time_str else None,
            created_at=datetime.now()
        )
        db.session.add(story)
        db.session.flush()

        # Optional schedule entry
        if schedule_time_str:
            schedule = StorySchedule(
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

    story_data = []

    for s in stories:
        file_path = s.video_path or s.image_path
        story_data.append({
            "id": s.id,
            "caption": s.caption.strip() if s.caption else "",
            "created_at": s.created_at.strftime("%Y-%m-%d %H:%M"),
            "filename": os.path.basename(file_path) if file_path else None,
            "media_type": s.media_type,   # ✅ pass type so template knows <img> vs <video>
            "status": s.status,
            "scheduled_at": s.scheduled_at.strftime("%Y-%m-%d %H:%M") if s.scheduled_at else None
        })

    return render_template(
        "stories.html",
        user=user_email,
        stories=story_data
    )


# ================================================
# Serve Story Media
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

        # Delete schedules
        schedules = StorySchedule.query.filter_by(user_id=user_id, story_id=story.id).all()
        for schedule in schedules:
            db.session.delete(schedule)
        db.session.commit()

        # Delete file
        filename = os.path.basename(story.video_path or story.image_path)
        file_path = os.path.join(get_output_dir(user_email), "stories", filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            deleted_any = True

        db.session.delete(story)
        db.session.commit()
        flash(f"🗑️ Deleted story: {filename}", "info" if deleted_any else "warning")

    except Exception as e:
        logger.error(f"[Delete Story] Error deleting story ID {story_id}: {e}")
        flash("❌ Error while deleting story.", "error")

    return redirect(url_for("stories.list_stories"))

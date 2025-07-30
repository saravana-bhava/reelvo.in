# ================================================
# File:         routes/reels.py
# Description:  No description provided.
# Framework:    Flask + TailwindCSS
# Version:      1.0.0
# Last Updated: 31 July 2025
# Author:       Saravana Bhava
# Author URL:   https://SazM.in
# ================================================

import os
import uuid
import glob
import logging
from threading import Thread
from datetime import datetime
from flask import (
    Blueprint, request, render_template, session, redirect,
    url_for, flash, jsonify, send_from_directory, current_app
)
from werkzeug.utils import secure_filename
from pydub.utils import mediainfo

from models import db, Reel
from models.schedule import Schedule
from utils.auth_decorator import login_required
from utils.auth_utils import get_user_id, get_user_email
from utils.generate_script import generate_script_for_user
from utils.reel_job import process_reel_job
from utils.progress_tracker import start_progress, get_progress

reels_bp = Blueprint("reels", __name__)
logger = logging.getLogger("create_reel")

if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

def get_output_dir(user_email):
    return os.path.join(current_app.config.get("OUTPUT_DIR", "output"), user_email)

def get_available_themes():
    try:
        from models.theme import Theme
        themes = Theme.query.with_entities(Theme.name).distinct().order_by(Theme.name.asc()).all()
        return [t.name for t in themes]
    except Exception as e:
        logger.error(f"Error loading themes from DB: {e}")
        return []

@reels_bp.route("/create-reel", methods=["GET"])
@login_required
def create_reel():
    if session.get("reel_in_progress"):
        return redirect(url_for("reels.reel_progress", task_id=session["reel_in_progress"]))

    user_email = get_user_email()
    user_id = get_user_id()
    output_dir = get_output_dir(user_email)
    videos_dir = os.path.join(output_dir, "videos")
    scripts_dir = os.path.join(output_dir, "scripts")
    os.makedirs(videos_dir, exist_ok=True)
    os.makedirs(scripts_dir, exist_ok=True)

    reels = Reel.query.filter_by(user_id=user_id).order_by(Reel.created_at.desc()).all()
    videos = [r.video_path for r in reels]
    scripts = sorted([f for f in os.listdir(scripts_dir) if f.endswith(".txt")], reverse=True)
    themes = get_available_themes()

    return render_template(
        "create_reel.html",
        user=user_email,
        videos=videos,
        themes=themes,
        selected_theme=request.args.get("theme", ""),
        custom_topic=request.args.get("custom_topic", ""),
        language=request.args.get("language", "en"),
        voice_option=request.args.get("voice_option", "tts"),
        voice_artist=request.args.get("voice_artist", ""),
        script_text=request.args.get("script", ""),
        subtitles_checked="subtitles" in request.args,
        watermark_checked="watermark" in request.args
    )

@reels_bp.route("/create", methods=["POST"])
@login_required
def create_reel_action():
    user_email = get_user_email()
    user_id = get_user_id()

    if not user_email or not user_id:
        logger.error("❌ Session missing email or user_id.")
        flash("Your session has expired. Please log in again.", "error")
        return redirect(url_for("auth.index"))

    from models.user import User
    user = db.session.query(User).filter_by(id=user_id).first()
    if not user:
        flash("Invalid user. Please log in again.", "error")
        return redirect(url_for("auth.index"))

    theme = request.form.get("theme", "").strip()
    custom_topic = request.form.get("custom_topic", "").strip()
    language = request.form.get("language", "en").strip()
    script_text = request.form.get("script", "").strip()
    use_tts = request.form.get("voice_option") == "tts"
    voice = request.form.get("voice_artist", "").strip()
    custom_voice_file = request.files.get("custom_voice")
    subtitles_enabled = "subtitles" in request.form
    watermark_enabled = "watermark" in request.form

    def redirect_with_form_data(msg):
        flash(msg, "error")
        return redirect(url_for("reels.create_reel",
            theme=theme,
            custom_topic=custom_topic,
            language=language,
            voice_option="tts" if use_tts else "upload",
            voice_artist=voice,
            script=script_text,
            subtitles="1" if subtitles_enabled else "",
            watermark="1" if watermark_enabled else ""
        ))

    if not (theme or custom_topic):
        return redirect_with_form_data("You must select a theme or enter a custom topic.")
    if not script_text:
        return redirect_with_form_data("Script is required.")
    if use_tts and not voice:
        return redirect_with_form_data("Please select a voice for TTS.")
    if not use_tts and not custom_voice_file:
        return redirect_with_form_data("You must upload a voice file or choose TTS.")

    raw_theme = custom_topic or theme or "default"
    if len(raw_theme) > 100:
        return redirect_with_form_data("Topic name too long.")

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    theme_name = secure_filename(raw_theme.replace(" ", "_")) + "_" + timestamp

    audio_path = None
    if custom_voice_file:
        user_audio_dir = os.path.join(get_output_dir(user_email), "tts")
        os.makedirs(user_audio_dir, exist_ok=True)
        tts_filename = f"{theme_name}_{language}_voice.mp3".replace(" ", "_")
        audio_path = os.path.join(user_audio_dir, tts_filename)
        custom_voice_file.save(audio_path)

        try:
            info = mediainfo(audio_path)
            duration_seconds = float(info["duration"])
            if duration_seconds > 30:
                os.remove(audio_path)
                return redirect_with_form_data("Uploaded voice file must be 30 seconds or less.")
        except Exception as e:
            logger.error(f"Error checking audio duration: {e}")
            return redirect_with_form_data("Could not validate voice file duration.")

    task_id = str(uuid.uuid4())
    session["reel_in_progress"] = task_id
    start_progress(task_id, user_id)

    def run_job_in_context(app, task_id):
        with app.app_context():
            process_reel_job(
                task_id,
                user_id,
                user_email,
                theme_name,
                language,
                script_text,
                use_tts,
                voice,
                custom_voice_file,
                subtitles_enabled,
                watermark_enabled
            )

    app = current_app._get_current_object()
    thread = Thread(target=run_job_in_context, args=(app, task_id))
    thread.daemon = True
    thread.start()

    return render_template("reel_progress.html", task_id=task_id)

@reels_bp.route("/progress/<task_id>")
@login_required
def progress_status(task_id):
    try:
        status = get_progress(task_id)
        if not status:
            session.pop("reel_in_progress", None)
            return jsonify({
                "percent": -1,
                "message": "❌ Task not found.",
                "done": True,
                "elapsed": 0
            }), 404

        percent = status.get("percent", 0)
        done = percent >= 100
        if done:
            session.pop("reel_in_progress", None)

        return jsonify({
            "percent": percent,
            "message": status.get("status", "Working..."),
            "elapsed": status.get("elapsed", 0),
            "done": done,
            "download_url": status.get("download_url", "")
        })
    except Exception as e:
        logger.error(f"[Progress Status] Error fetching progress for {task_id}: {e}")
        return jsonify({
            "percent": -1,
            "message": "❌ Internal error while checking progress.",
            "done": True
        }), 500

@reels_bp.route("/reel_progress/<task_id>")
@login_required
def reel_progress(task_id):
    status = get_progress(task_id)
    if status.get("percent", -1) == -1 or status.get("percent", 0) >= 100:
        session.pop("reel_in_progress", None)
        return redirect(url_for("reels.create_reel"))
    return render_template("reel_progress.html", task_id=task_id)

@reels_bp.route("/generate-script", methods=["POST"])
@login_required
def generate_script_ajax():
    try:
        data = request.get_json()
        user_email = get_user_email()
        custom_topic = data.get("custom_topic", "").strip()
        theme = data.get("theme")
        language = data.get("language", "en")

        if not theme and not custom_topic:
            return jsonify({"error": "Please provide a theme or custom topic."}), 400

        raw_theme = custom_topic or theme or "default"
        if len(raw_theme) > 100:
            return jsonify({"error": "Topic name too long."}), 400

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        theme_name = secure_filename(raw_theme.replace(" ", "_")) + "_" + timestamp

        script_path = generate_script_for_user(
            user_email=user_email,
            folder_name="scripts",
            theme_name=theme_name,
            language=language,
            prompt=custom_topic or theme
        )
        with open(script_path, encoding="utf-8") as f:
            return jsonify({"script_text": f.read().strip()})
    except Exception as e:
        logger.exception("Script generation failed")
        return jsonify({"error": str(e)}), 500

@reels_bp.route("/videos/<user_email>/<filename>")
def serve_video(user_email, filename):
    return send_from_directory(os.path.join(get_output_dir(user_email), "videos"), filename)

@reels_bp.route("/reel-history", methods=["GET"])
@login_required
def list_reels():
    user_email = get_user_email()
    user_id = get_user_id()

    reels = Reel.query.filter_by(user_id=user_id).order_by(Reel.created_at.desc()).all()

    videos = []
    scripts = {}
    vid_date_map = {}
    title_map = {}
    file_map = {}

    for r in reels:
        reel_id = r.id
        filename = os.path.basename(r.video_path)
        videos.append(reel_id)
        scripts[reel_id] = r.script.strip() if r.script else ""
        vid_date_map[reel_id] = r.created_at.strftime("%Y-%m-%d %H:%M")
        title_map[reel_id] = r.title or (r.theme_name.replace("_", " ").strip().title() if r.theme_name else filename)
        file_map[reel_id] = filename

    return render_template(
        "reels.html",
        user=user_email,
        videos=videos,
        scripts=scripts,
        vid_date_map=vid_date_map,
        title_map=title_map,
        file_map=file_map
    )

@reels_bp.route("/reels/delete/<int:reel_id>", methods=["POST"])
@login_required
def delete_reel(reel_id):
    user_email = get_user_email()
    user_id = get_user_id()

    deleted_any = False
    try:
        reel = Reel.query.filter_by(user_id=user_id, id=reel_id).first()
        if not reel:
            flash("⚠️ Reel not found or already deleted.", "warning")
            return redirect(url_for("reels.list_reels"))

        schedules = Schedule.query.filter_by(user_id=user_id, reel_id=reel.id).all()
        for schedule in schedules:
            db.session.delete(schedule)

        filename = os.path.basename(reel.video_path)
        base_video = os.path.splitext(filename)[0]
        base_path = get_output_dir(user_email)

        db.session.delete(reel)
        db.session.commit()

        targets = {
            "video": os.path.join(base_path, "videos", filename),
            "image": os.path.join(base_path, "images", base_video.replace("_video", "_text_image") + ".png"),
            "script": os.path.join(base_path, "scripts", base_video.replace("_video", "_text") + ".txt"),
            "ass": os.path.join(base_path, "srt", base_video.replace("_video", "_srt") + ".ass"),
            "srt": os.path.join(base_path, "srt", base_video.replace("_video", "_srt") + ".srt"),
            "temp_concat_list": os.path.join(base_path, "temp", "concat_list.txt"),
            "tts": os.path.join(base_path, "tts", base_video.replace("_video", "_voice") + ".mp3"),
            "tts_raw": os.path.join(base_path, "tts", base_video.replace("_video", "_voice_raw") + ".mp3"),
        }

        temp_dir = os.path.join(base_path, "temp")
        if os.path.exists(temp_dir):
            base_video_clean = base_video.replace("_video", "").rsplit(".", 1)[0]
            for pattern in [os.path.join(temp_dir, f"{base_video_clean}*.mp4"),
                            os.path.join(temp_dir, f"{base_video_clean}*.m4a")]:
                for f in glob.glob(pattern):
                    os.remove(f)
                    deleted_any = True

        for path in targets.values():
            if os.path.exists(path):
                os.remove(path)
                deleted_any = True

        flash(f"🗑️ Deleted reel: {reel.title or filename}", "info" if deleted_any else "warning")
    except Exception as e:
        logger.error(f"[Delete Reel] Error deleting reel ID {reel_id}: {e}")
        flash("❌ Error while deleting reel.", "error")

    return redirect(url_for("reels.list_reels"))

# File: routes/reels.py

import os
import json
import logging
import uuid
from threading import Thread
from flask import (
    Blueprint, request, render_template, session, redirect,
    url_for, flash, jsonify, send_from_directory
)
from werkzeug.utils import secure_filename
from utils.generate_script import generate_script_for_user
from utils.reel_job import generate_reel_background
from utils.progress_tracker import start_progress, get_progress

reels_bp = Blueprint("reels", __name__)
logger = logging.getLogger("create_reel")
logging.basicConfig(level=logging.INFO)

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
THEME_JSON_PATH = os.path.join(ROOT_DIR, "theme.json")

@reels_bp.route("/create-reel", methods=["GET"])
def create_reel():
    if "user" not in session:
        return redirect(url_for("auth.index"))

    # 🔒 Prevent access if reel in progress
    if session.get("reel_in_progress"):
        return redirect(url_for("reels.reel_progress", task_id=session["reel_in_progress"]))

    user_email = session["user"]
    output_dir = os.path.join("output", user_email)
    videos_dir = os.path.join(output_dir, "videos")
    scripts_dir = os.path.join(output_dir, "scripts")
    os.makedirs(videos_dir, exist_ok=True)
    os.makedirs(scripts_dir, exist_ok=True)

    videos = os.listdir(videos_dir)
    scripts = sorted([f for f in os.listdir(scripts_dir) if f.endswith(".txt")], reverse=True)

    latest_script = ""
    with open(THEME_JSON_PATH, encoding="utf-8") as f:
        themes = sorted(json.load(f).keys())

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
        script_text=request.args.get("script", latest_script),
        subtitles_checked="subtitles" in request.args,
        watermark_checked="watermark" in request.args
    )

@reels_bp.route("/create", methods=["POST"])
def create_reel_action():
    if "user" not in session:
        return redirect(url_for("auth.index"))

    user_email = session["user"]
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

    theme_name = secure_filename(raw_theme)
    audio_path = None
    if custom_voice_file:
        user_audio_dir = os.path.join("output", user_email, "tts")
        os.makedirs(user_audio_dir, exist_ok=True)
        tts_filename = f"{theme_name}_{language}_voice.mp3"
        audio_path = os.path.join(user_audio_dir, tts_filename)
        custom_voice_file.save(audio_path)

    task_id = str(uuid.uuid4())
    session["reel_in_progress"] = task_id
    start_progress(task_id)

    Thread(target=generate_reel_background, args=(
        task_id,
        user_email,
        theme_name,
        language,
        script_text,
        use_tts,
        voice,
        custom_voice_file,
        subtitles_enabled,
        watermark_enabled
    )).start()

    return render_template("reel_progress.html", task_id=task_id)

@reels_bp.route("/progress/<task_id>")
def progress_status(task_id):
    try:
        status = get_progress(task_id)

        if not status:
            session.pop("reel_in_progress", None)
            session.pop("current_task", None)
            return jsonify({
                "percent": -1,
                "message": "❌ Task not found.",
                "done": True,
                "elapsed": 0
            }), 404

        percent = status.get("percent", 0)
        message = status.get("status", "Working...")
        elapsed = status.get("elapsed", 0)
        done = percent >= 100

        if done:
            session.pop("reel_in_progress", None)

        return jsonify({
            "percent": percent,
            "message": message,
            "elapsed": elapsed,
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
def reel_progress(task_id):
    status = get_progress(task_id)

    # If task not found or already complete, clear session and redirect
    if status.get("percent", -1) == -1 or status.get("percent", 0) >= 100:
        session.pop("reel_in_progress", None)
        return redirect(url_for("reels.create_reel"))

    return render_template("reel_progress.html", task_id=task_id)

@reels_bp.route("/generate-script", methods=["POST"])
def generate_script_ajax():
    try:
        data = request.get_json()
        user_email = session["user"]
        topic = data.get("custom_topic", "").strip()
        theme = data.get("theme")
        language = data.get("language", "en")

        if not theme and not topic:
            return jsonify({"error": "Please provide a theme or custom topic."}), 400

        script_path = generate_script_for_user(
            user_email=user_email,
            folder_name="scripts",
            theme_name=topic or theme,
            language=language,
            prompt=topic or theme
        )
        with open(script_path, encoding="utf-8") as f:
            return jsonify({"script_text": f.read().strip()})
    except Exception as e:
        logger.exception("Script generation failed")
        return jsonify({"error": str(e)}), 500

@reels_bp.route("/videos/<user_email>/<filename>")
def serve_video(user_email, filename):
    return send_from_directory(os.path.join("output", user_email, "videos"), filename)

@reels_bp.route("/reel-history", methods=["GET"])
def list_reels():
    if "user" not in session:
        return redirect(url_for("auth.index"))

    user_email = session["user"]
    video_folder = os.path.join("output", user_email, "videos")
    os.makedirs(video_folder, exist_ok=True)

    videos = [f for f in os.listdir(video_folder) if f.endswith(".mp4")]

    scripts_path = os.path.join("output", user_email, "scripts")
    scripts = {}
    if os.path.exists(scripts_path):
        for f in os.listdir(scripts_path):
            if f.endswith(".txt"):
                with open(os.path.join(scripts_path, f), encoding="utf-8") as file:
                    scripts[f.replace("_text.txt", "_video.mp4")] = file.read().strip()

    return render_template("reels.html", user=user_email, videos=videos, scripts=scripts)

@reels_bp.route("/reels/delete/<filename>", methods=["POST"])
def delete_reel(filename):
    if "user" not in session:
        return redirect(url_for("auth.index"))

    user_email = session["user"]
    base_video = os.path.splitext(filename)[0]
    base_path = os.path.join("output", user_email)

    deleted_any = False
    try:
        targets = {
            "video": os.path.join(base_path, "videos", filename),
            "image": os.path.join(base_path, "images", base_video.replace("_video", "_text_image") + ".png"),
            "script": os.path.join(base_path, "scripts", base_video.replace("_video", "_text") + ".txt"),
            "srt": os.path.join(base_path, "srt", base_video.replace("_video", "_srt") + ".srt"),
            "temp_concat_list": os.path.join(base_path, "temp", "concat_list.txt"),
            "tts": os.path.join(base_path, "tts", base_video.replace("_video", "_voice") + ".mp3"),
            "tts_raw": os.path.join(base_path, "tts", base_video.replace("_video", "_voice_raw") + ".mp3"),
        }

        # --- Delete temp files using glob ---
        import glob

        temp_dir = os.path.join(base_path, "temp")
        if os.path.exists(temp_dir):
            base_video_clean = base_video.replace("_video", "").rsplit(".", 1)[0]
            temp_patterns = [
                os.path.join(temp_dir, f"{base_video_clean}*.mp4"),
                os.path.join(temp_dir, f"{base_video_clean}*.m4a"),
            ]
            for pattern in temp_patterns:
                for f in glob.glob(pattern):
                    os.remove(f)
                    deleted_any = True

        # --- Delete known target files ---
        for path in targets.values():
            if os.path.exists(path):
                os.remove(path)
                deleted_any = True

        flash(f"🗑️ Deleted reel: {filename}", "info" if deleted_any else "warning")
    except Exception as e:
        logger.error(f"[Delete Reel] Error deleting {filename}: {e}")
        flash("❌ Error while deleting reel.", "error")

    return redirect(url_for("reels.list_reels"))

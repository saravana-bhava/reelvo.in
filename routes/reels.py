# File: routes/reels.py

import os
import json
from flask import (
    Blueprint, request, render_template, session, redirect,
    url_for, flash, jsonify, send_from_directory
)
from werkzeug.utils import secure_filename

from utils.generate_script import generate_script_for_user
from utils.create_video import create_video_for_category
from utils.google_drive import upload_to_google_drive
from utils.generate_tts_audio import generate_tts_audio
from utils.instagram import post_to_instagram
from utils.subtitles import generate_srt_from_audio

reels_bp = Blueprint("reels", __name__)

@reels_bp.route("/create", methods=["GET"])
def create_reel():
    if "user" not in session:
        return redirect(url_for("auth.index"))

    user = session["user"]
    output_path = os.path.join("output", user)
    os.makedirs(output_path, exist_ok=True)
    videos = os.listdir(output_path)

    # Load latest saved script
    script = ""
    user_script_dir = os.path.join("output", user, "scripts")
    os.makedirs(user_script_dir, exist_ok=True)
    scripts = sorted(
        [f for f in os.listdir(user_script_dir) if f.endswith(".txt")],
        reverse=True
    )
    if scripts:
        with open(os.path.join(user_script_dir, scripts[0]), "r", encoding="utf-8") as f:
            script = f.read()

    # Load themes from theme.json
    theme_path = os.path.join("theme.json")
    with open(theme_path, "r", encoding="utf-8") as f:
        theme_data = json.load(f)
    themes = sorted(theme_data.keys())

    return render_template(
        "create_reel.html",
        user=user,
        videos=videos,
        script=script,
        themes=themes
    )

@reels_bp.route("/create", methods=["POST"])
def create_reel_action():
    """Handle reel generation and processing."""
    if "user" not in session:
        return redirect(url_for("auth.index"))

    user = session["user"]
    theme = request.form.get("theme")
    custom_topic = request.form.get("custom_topic", "").strip()
    language = request.form.get("language", "en")
    script = request.form.get("script", "").strip()
    use_tts = request.form.get("voice_option") == "tts"
    voice = request.form.get("voice_artist")
    subtitles_enabled = "subtitles" in request.form
    watermark_enabled = "watermark" in request.form
    custom_voice_file = request.files.get("custom_voice")

    output_dir = os.path.join("output", user)
    os.makedirs(output_dir, exist_ok=True)

    if not script:
        flash("Script is required.", "error")
        return redirect(url_for("reels.create_reel"))

    # Save script to file
    script_dir = os.path.join("output", user, "scripts")
    os.makedirs(script_dir, exist_ok=True)
    script_filename = f"script_{language}_{user}_{len(os.listdir(script_dir)) + 1}.txt"
    script_path = os.path.join(script_dir, secure_filename(script_filename))
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script)

    video_filename = f"{theme or custom_topic}_{language}_{user}.mp4"
    video_path = os.path.join(output_dir, secure_filename(video_filename))

    # TTS Audio or Uploaded Voice
    audio_path, marks_path = None, None
    if use_tts:
        audio_path, marks_path = generate_tts_audio(script, language, voice, output_dir)
    elif custom_voice_file:
        filename = secure_filename(custom_voice_file.filename)
        audio_path = os.path.join(output_dir, filename)
        custom_voice_file.save(audio_path)
    else:
        flash("You must upload a voice file or choose TTS.", "error")
        return redirect(url_for("reels.create_reel"))

    # Create Reel
    create_video_for_category(
        category=theme or "custom",
        script_text=script,
        audio_path=audio_path,
        output_path=video_path,
        language=language,
        include_subtitles=subtitles_enabled,
        include_watermark=watermark_enabled,
        tts_marks_path=marks_path,
        username=user,
    )

    # Upload to Google Drive
    upload_url = upload_to_google_drive(video_path, user)
    flash(f"✅ Reel created and uploaded! Download: {upload_url}", "success")

    return redirect(url_for("reels.create_reel"))


@reels_bp.route("/generate-script", methods=["POST"])
def generate_script_ajax():
    """AJAX endpoint to generate script dynamically."""
    data = request.get_json()
    topic = data.get("custom_topic", "").strip()
    theme = data.get("theme")
    language = data.get("language", "en")
    username = session["user"]

    if not theme and not topic:
        return jsonify({"error": "Please provide a theme or custom topic."}), 400

    try:
        script_path = generate_script_for_user(topic if topic else theme, username, language)
        with open(script_path, "r", encoding="utf-8") as f:
            script = f.read().strip()
        return jsonify({"script": script})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reels_bp.route("/videos/<username>/<filename>")
def serve_video(username, filename):
    """Serve previously generated video to user."""
    return send_from_directory(os.path.join("output", username), filename)


@reels_bp.route("/reels", methods=["GET"])
def list_reels():
    """List all previously generated reels."""
    if "user" not in session:
        return redirect(url_for("auth.index"))

    user = session["user"]
    video_folder = os.path.join("output", user)
    os.makedirs(video_folder, exist_ok=True)

    videos = [f for f in os.listdir(video_folder) if f.endswith(".mp4")]
    return render_template("reels.html", user=user, videos=videos)

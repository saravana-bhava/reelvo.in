# File: routes/reels.py

import os
import json
import logging
from flask import (
    Blueprint, request, render_template, session, redirect,
    url_for, flash, jsonify, send_from_directory
)
from werkzeug.utils import secure_filename

from utils.generate_script import generate_script_for_user
from utils.generate_text_overlay import generate_text_overlay
from utils.generate_tts_audio import generate_tts_from_text
from utils.subtitles import generate_srt_from_audio
from utils.create_video import create_video_for_theme
from utils.google_drive import upload_to_google_drive
from utils.instagram import post_to_instagram

reels_bp = Blueprint("reels", __name__)

# Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("create_video")

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

    username = session["user"]
    theme = request.form.get("theme")
    custom_topic = request.form.get("custom_topic", "").strip()
    language = request.form.get("language", "en")
    script = request.form.get("script", "").strip()
    use_tts = request.form.get("voice_option") == "tts"
    voice = request.form.get("voice_artist")
    subtitles_enabled = "subtitles" in request.form
    watermark_enabled = "watermark" in request.form
    custom_voice_file = request.files.get("custom_voice")

    output_dir = os.path.join("output", username)
    os.makedirs(output_dir, exist_ok=True)

    if not script:
        flash("Script is required.", "error")
        return redirect(url_for("reels.create_reel"))

    logger.info(f"🎬 Starting reel for: {theme.upper() or custom_topic.upper()} | User: {username} | Lang: {language}")

    # Save script to file
    script_dir = os.path.join("output", username, "scripts")
    os.makedirs(script_dir, exist_ok=True)

    script_filename = f"{theme or custom_topic}_{language}_text.txt"
    script_path = os.path.join(script_dir, secure_filename(script_filename))

    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script)

    logger.info(f"🖼️ Generating overlay...")
    text_image_path = os.path.join(output_dir, "image", f"{theme or custom_topic}_{language}_text_image.png")
    generate_text_overlay(script, text_image_path, language=language)

    video_filename = f"{theme or custom_topic}_{language}_video.mp4"
    video_path = os.path.join(output_dir, "videos", secure_filename(video_filename))

    # TTS Audio or Uploaded Voice
    logger.info(f"🔊 Generating TTS...")
    audio_path = os.path.join(output_dir, "tts", f"{theme or custom_topic}_{language}_voice.mp3")
    if use_tts:
        audio_path = generate_tts_from_text(script, username, audio_path, theme or custom_topic, None, language, voice)
    elif custom_voice_file:
        logger.info("[🔊] Using uploaded voiceover...")
        filename = secure_filename(custom_voice_file.filename)
        audio_path = os.path.join(output_dir, "tts", filename)
        voiceover_path.save(audio_path)
        audio_duration = float(subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries",
            "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
            audio_path
        ]).strip())
    else:
        flash("You must upload a voice file or choose TTS.", "error")
        return redirect(url_for("reels.create_reel"))

    if subtitles_enabled:
        logger.info(f"📝 Generating subtitles...")
        srt_path = os.path.join(output_dir, "srt", f"{theme or custom_topic}_{language}_srt.srt")
        logger.info(audio_path)
        generate_srt_from_audio(theme or custom_topic, audio_path, srt_path, 6, None, language=language)

    # Create Reel
#    create_video_for_theme(
#        category=theme or "custom",
#        username=username,
#        include_watermark=watermark_enabled,
#        bgm_path=None,
#        language=language,
#        task_id=None,
#        script_text=script,
#        voiceover_path=audio_path,
#        tts_voice=voice,
#        include_subtitles=subtitles_enabled,
#    )

    # Upload to Google Drive
    upload_url = upload_to_google_drive(video_path, username)
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

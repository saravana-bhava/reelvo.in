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
from utils.generate_tts_audio import generate_tts_audio
from utils.generate_srt_from_audio import generate_srt_from_audio
from utils.translate_text import translate_to_english
from utils.fetch_multiple_clips import fetch_multiple_clips, concatenate_clips
from utils.create_video import create_video_for_theme
from utils.google_drive import upload_to_google_drive
from utils.instagram import post_to_instagram

reels_bp = Blueprint("reels", __name__)

# Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("create_reel")

@reels_bp.route("/create", methods=["GET"])
def create_reel():
    if "user" not in session:
        return redirect(url_for("auth.index"))

    user = session["user"]
    output_path = os.path.join("output", user)
    os.makedirs(output_path, exist_ok=True)
    videos = os.listdir(output_path)

    # Load latest saved script_text
    script_text = ""
    user_script_dir = os.path.join("output", user, "scripts")
    os.makedirs(user_script_dir, exist_ok=True)
    scripts = sorted(
        [f for f in os.listdir(user_script_dir) if f.endswith(".txt")],
        reverse=True
    )
    if scripts:
        with open(os.path.join(user_script_dir, scripts[0]), "r", encoding="utf-8") as f:
            script_text = f.read()

    # Load themes from theme.json
    theme_path = os.path.join("theme.json")
    with open(theme_path, "r", encoding="utf-8") as f:
        theme_data = json.load(f)
    themes = sorted(theme_data.keys())

    return render_template(
        "create_reel.html",
        user=user,
        videos=videos,
        script_text=script_text,
        themes=themes
    )

@reels_bp.route("/create", methods=["POST"])
def create_reel_action():
    """Handle reel generation and processing."""
    if "user" not in session:
        return redirect(url_for("auth.index"))

    user_name = session["user"]
    theme = request.form.get("theme")
    custom_topic = request.form.get("custom_topic", "").strip()
    language = request.form.get("language", "en")
    script_text = request.form.get("script", "").strip()
    use_tts = request.form.get("voice_option") == "tts"
    voice = request.form.get("voice_artist")
    custom_voice_file = request.files.get("custom_voice")
    subtitles_enabled = "subtitles" in request.form
    watermark_enabled = "watermark" in request.form
    theme_name = custom_topic if custom_topic else theme

    if not script_text:
        flash("Script is required.", "error")
        return redirect(url_for("reels.create_reel"))

    logger.info(f"🎬 Starting reel for: User: {user_name} | Theme: {theme_name} | Language: {language}")

    output_dir = os.path.join("output", user_name)
    os.makedirs(output_dir, exist_ok=True)

    # Save script_text to file
    scripts_dir = os.path.join(output_dir, "scripts")
    os.makedirs(scripts_dir, exist_ok=True)
    script_filename = f"{theme_name}_{language}_text.txt"
    script_path = os.path.join(scripts_dir, secure_filename(script_filename))

    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script_text)

    # Generate Text Image Overlay
    images_dir = os.path.join(output_dir, "images")
    os.makedirs(images_dir, exist_ok=True)
    text_image_filename = f"{theme_name}_{language}_text_image.png"
    text_image_path = os.path.join(images_dir, secure_filename(text_image_filename))

    generate_text_overlay(text_image_path, language, script_text)

    # TTS Audio or Uploaded Voice
    tts_dir = os.path.join(output_dir, "tts")
    os.makedirs(tts_dir, exist_ok=True)
    tts_filename = f"{theme_name}_{language}_voice.mp3"
    audio_path = os.path.join(tts_dir, secure_filename(tts_filename))

    if use_tts:
        audio_path, audio_duration = generate_tts_audio(
            tts_path=audio_path,
            language=language,
            script_text=script_text,
            tts_voice=voice,
            cache=True
        )
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
        srt_dir = os.path.join(output_dir, "srt")
        os.makedirs(srt_dir, exist_ok=True)
        srt_filename = f"{theme_name}_{language}_srt.srt"
        srt_path = os.path.join(srt_dir, secure_filename(srt_filename))

        generate_srt_from_audio(
            srt_path=srt_path,
            language=language,
            audio_path=audio_path,
            words_per_line=6
        )

    english_script_text = translate_to_english(script_text)

    temp_dir = os.path.join(output_dir, "temp")
    os.makedirs(temp_dir, exist_ok=True)
    clips = fetch_multiple_clips(
        temp_dir=temp_dir,
        theme_name=theme_name,
        language=language,
        script_text=english_script_text,
        target_duration=audio_duration
    )
    if not clips:
        logger.error("[❌] No video clips found.")
        flash("[❌] No video clips found.", "error")
        return redirect(url_for("reels.create_reel"))

    combined_video_path = concatenate_clips(
        temp_dir=temp_dir,
        theme_name=theme_name,
        language=language,
        clips=clips
    )
    if not combined_video_path:
        logger.error("[❌] Video clips could not be combined.")
        flash("[❌] Video clips could not be combined.", "error")
        return redirect(url_for("reels.create_reel"))

    # Create Reel
#    video_filename = f"{theme or custom_topic}_{language}_video.mp4"
#    video_path = os.path.join(output_dir, "videos", secure_filename(video_filename))

#    create_video_for_theme(
#        category=theme or "custom",
#        user_name=user_name,
#        include_watermark=watermark_enabled,
#        bgm_path=None,
#        language=language,
#        task_id=None,
#        script_text=script_text,
#        voiceover_path=audio_path,
#        tts_voice=voice,
#        include_subtitles=subtitles_enabled,
#    )

    # Upload to Google Drive
#    upload_url = upload_to_google_drive(video_path, user_name)
#    flash(f"✅ Reel created and uploaded! Download: {upload_url}", "success")

#    return redirect(url_for("reels.create_reel"))
    return "Done"

@reels_bp.route("/generate-script", methods=["POST"])
def generate_script_ajax():
    """AJAX endpoint to generate script dynamically."""
    data = request.get_json()
    user_name = session["user"]
    topic = data.get("custom_topic", "").strip()
    theme = data.get("theme")
    language = data.get("language", "en")

    if not theme and not topic:
        return jsonify({"error": "Please provide a theme or custom topic."}), 400

    try:
        script_path = generate_script_for_user(
            user_name = user_name,
            folder_name = "scripts",
            theme_name = topic if topic else theme,
            language = language,
            prompt = topic if topic else theme
        )
        with open(script_path, "r", encoding="utf-8") as f:
            script_text = f.read().strip()
        return jsonify({"script_text": script_text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reels_bp.route("/videos/<user_name>/<filename>")
def serve_video(user_name, filename):
    """Serve previously generated video to user."""
    return send_from_directory(os.path.join("output", user_name), filename)


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

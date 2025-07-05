# File: routes/reels.py

import os
import json
import logging
import subprocess
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
from utils.fetch_bgm import fetch_bgm
from utils.fetch_multiple_clips import fetch_multiple_clips, concatenate_clips
from utils.create_video import create_video
from utils.google_drive import upload_to_google_drive
from utils.instagram import post_to_instagram
from utils.reel_history import add_reel_to_history

reels_bp = Blueprint("reels", __name__)

logger = logging.getLogger("create_reel")
logging.basicConfig(level=logging.INFO)


@reels_bp.route("/create", methods=["GET"])
def create_reel():
    if "user" not in session:
        return redirect(url_for("auth.index"))

    user_email = session["user"]
    videos_path = os.path.join("output", user_email, "videos")
    os.makedirs(videos_path, exist_ok=True)
    videos = os.listdir(videos_path)

    script_text = ""
    user_script_dir = os.path.join("output", user_email, "scripts")
    os.makedirs(user_script_dir, exist_ok=True)
    scripts = sorted(
        [f for f in os.listdir(user_script_dir) if f.endswith(".txt")],
        reverse=True
    )
    if scripts:
        with open(os.path.join(user_script_dir, scripts[0]), "r", encoding="utf-8") as f:
            script_text = f.read()

    theme_path = "theme.json"
    with open(theme_path, "r", encoding="utf-8") as f:
        theme_data = json.load(f)
    themes = sorted(theme_data.keys())

    return render_template(
        "create_reel.html",
        user=user_email,
        videos=videos,
        script_text=script_text,
        themes=themes
    )


@reels_bp.route("/create", methods=["POST"])
def create_reel_action():
    if "user" not in session:
        return redirect(url_for("auth.index"))

    user_email = session["user"]
    theme = request.form.get("theme")
    custom_topic = request.form.get("custom_topic", "").strip()
    language = request.form.get("language", "en")
    script_text = request.form.get("script", "").strip()
    use_tts = request.form.get("voice_option") == "tts"
    voice = request.form.get("voice_artist")
    custom_voice_file = request.files.get("custom_voice")
    subtitles_enabled = "subtitles" in request.form
    watermark_enabled = "watermark" in request.form
    theme_name = secure_filename(custom_topic if custom_topic else theme)

    if not script_text:
        flash("Script is required.", "error")
        return redirect(url_for("reels.create_reel"))

    logger.info(f"🎬 Starting reel for: User: {user_email} | Theme: {theme_name} | Language: {language}")

    output_dir = os.path.join("output", user_email)
    scripts_dir = os.path.join(output_dir, "scripts")
    images_dir = os.path.join(output_dir, "images")
    tts_dir = os.path.join(output_dir, "tts")
    os.makedirs(scripts_dir, exist_ok=True)
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(tts_dir, exist_ok=True)

    script_filename = f"{theme_name}_{language}_text.txt"
    script_path = os.path.join(scripts_dir, secure_filename(script_filename))
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script_text)

    text_image_filename = f"{theme_name}_{language}_text_image.png"
    text_image_path = os.path.join(images_dir, secure_filename(text_image_filename))
    generate_text_overlay(text_image_path, language, script_text)

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
        audio_path = os.path.join(tts_dir, filename)
        custom_voice_file.save(audio_path)
        audio_duration = float(subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries",
            "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
            audio_path
        ]).decode().strip())
    else:
        flash("You must upload a voice file or choose TTS.", "error")
        return redirect(url_for("reels.create_reel"))

    if audio_duration < 2.0:
        flash("Audio too short. Must be at least 2 seconds.", "error")
        return redirect(url_for("reels.create_reel"))

    if subtitles_enabled:
        srt_dir = os.path.join(output_dir, "srt")
        os.makedirs(srt_dir, exist_ok=True)
        srt_filename = f"{theme_name}_{language}_srt.srt"
        srt_path = os.path.join(srt_dir, secure_filename(srt_filename))
        generate_srt_from_audio(srt_path, language, audio_path, 6)

    english_script_text = translate_to_english(script_text)

    temp_dir = os.path.join(output_dir, "temp")
    os.makedirs(temp_dir, exist_ok=True)

    bgm_path = fetch_bgm(english_script_text, "en", "default") or "assets/music/default.mp3"
    mixed_filename = f"{theme_name}_{language}_mixed.m4a"
    mixed_audio_path = os.path.join(temp_dir, secure_filename(mixed_filename))
    audio_to_use = audio_path

    if bgm_path and os.path.exists(bgm_path):
        subprocess.run([
            "ffmpeg", "-y", "-i", audio_path, "-i", bgm_path,
            "-filter_complex", "[1:a]volume=0.1[a1];[0:a][a1]amix=inputs=2:duration=first:dropout_transition=2",
            "-c:a", "aac", "-b:a", "192k", mixed_audio_path
        ], check=True)
        audio_to_use = mixed_audio_path

    clips = fetch_multiple_clips(temp_dir, theme_name, language, english_script_text, audio_duration)
    if not clips:
        logger.error("[❌] No video clips found.")
        flash("[❌] No video clips found.", "error")
        return redirect(url_for("reels.create_reel"))

    combined_video_path = concatenate_clips(temp_dir, theme_name, language, clips)
    if not combined_video_path:
        logger.error("[❌] Video clips could not be combined.")
        flash("[❌] Video clips could not be combined.", "error")
        return redirect(url_for("reels.create_reel"))

    inputs = ["-i", combined_video_path, "-i", audio_to_use]
    input_index = 2
    logo_index = None

    if watermark_enabled:
        watermark_dir = os.path.join(output_dir, "watermark")
        os.makedirs(watermark_dir, exist_ok=True)
        watermark_path = os.path.join(watermark_dir, "logo.png")
        inputs += ["-loop", "1", "-t", str(audio_duration), "-i", watermark_path]
        logo_index = input_index
        input_index += 1

    filters = [
        f"[0:v]scale=1080:1920:force_original_aspect_ratio=decrease,"
        f"pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1,"
        f"fade=t=in:st=0:d=1,fade=t=out:st={max(audio_duration - 1, 1)}:d=1[bg]"
    ]
    base = "[bg]"

    if logo_index is not None:
        filters.append(f"{base}[{logo_index}:v]overlay=W-w-30:H-h-30[wm]")
        base = "[wm]"

    if subtitles_enabled:
        subtitle_style = (
            "Alignment=2,Fontname=DejaVuSans-Bold,Fontsize=16,"
            "PrimaryColour=&H00FFFFFF,OutlineColour=&H80000000,"
            "BorderStyle=3,Outline=2,MarginV=10"
        )
        escaped_srt_path = srt_path.replace('\\', '\\\\').replace(':', '\\:').replace("'", "\\'")
        filters.append(f"{base}subtitles='{escaped_srt_path}':force_style='{subtitle_style}'[outv]")
        map_video = "[outv]"
    else:
        map_video = base

    videos_dir = os.path.join(output_dir, "videos")
    os.makedirs(videos_dir, exist_ok=True)
    video_filename = f"{theme_name}_{language}_video.mp4"
    video_path = os.path.join(videos_dir, secure_filename(video_filename))

    video_path = create_video(video_path, inputs, audio_duration, filters, map_video)
    if not video_path:
        logger.error("[❌] Video could not be generated.")
        flash("[❌] Video could not be generated.", "error")
        return redirect(url_for("reels.create_reel"))

    logger.info("[🌐] Upload to Google Drive...")
    upload_url = upload_to_google_drive(video_path, user_email)
    flash(f"✅ Reel created and uploaded! Download: {upload_url}", "success")

    add_reel_to_history(user_email, os.path.basename(video_path), script_text)
    return redirect(url_for("reels.create_reel"))


@reels_bp.route("/generate-script", methods=["POST"])
def generate_script_ajax():
    data = request.get_json()
    user_email = session["user"]
    topic = data.get("custom_topic", "").strip()
    theme = data.get("theme")
    language = data.get("language", "en")

    if not theme and not topic:
        return jsonify({"error": "Please provide a theme or custom topic."}), 400

    try:
        script_path = generate_script_for_user(
            user_name=user_email,
            folder_name="scripts",
            theme_name=topic if topic else theme,
            language=language,
            prompt=topic if topic else theme
        )
        with open(script_path, "r", encoding="utf-8") as f:
            script_text = f.read().strip()
        return jsonify({"script_text": script_text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reels_bp.route("/videos/<user_email>/<filename>")
def serve_video(user_email, filename):
    return send_from_directory(os.path.join("output", user_email, "videos"), filename)


@reels_bp.route("/reels", methods=["GET"])
def list_reels():
    if "user" not in session:
        return redirect(url_for("auth.index"))

    user_email = session["user"]
    video_folder = os.path.join("output", user_email, "videos")
    os.makedirs(video_folder, exist_ok=True)

    videos = [f for f in os.listdir(video_folder) if f.endswith(".mp4")]
    return render_template("reels.html", user=user_email, videos=videos)

# ================================================
# File:         utils/reel_job.py
# Description:  Job scheduler logic for reel posting
# Framework:    Flask + TailwindCSS
# Version:      1.0.0
# Last Updated: 31 July 2025
# Author:       Saravana Bhava
# Author URL:   https://SazM.in
# ================================================

import os
import subprocess
import logging
import sys
import time
from flask import current_app
from datetime import datetime

from utils.generate_text_overlay import generate_text_overlay
from utils.generate_tts_audio import generate_tts_audio
from utils.generate_srt_from_audio import generate_srt_from_audio
from utils.translate_text import translate_to_english
from utils.fetch_bgm import fetch_bgm
from utils.fetch_multiple_clips import fetch_multiple_clips, concatenate_clips
from utils.create_video import create_video
from utils.google_drive import upload_to_google_drive
from utils.progress_tracker import (
    progress_status,
    start_progress,
    update_progress,
    finish_progress,
    get_stage_percent,
)

from models.reel import Reel
from models import db
from models.user import User

UPLOAD_TO_DRIVE = os.getenv("UPLOAD_TO_DRIVE", "false").strip().lower() == "true"
UPLOAD_TO_GOFILE = os.getenv("UPLOAD_TO_GOFILE", "false").strip().lower() == "true"
HOST = os.getenv("HOST", "reelvo.in")

ORIGINAL_STDOUT = sys.stdout
ORIGINAL_STDERR = sys.stderr


class StreamToLogger:
    def __init__(self, logger, level):
        self.logger = logger
        self.level = level

    def write(self, message):
        message = message.strip()
        if message:
            for line in message.splitlines():
                self.logger.log(self.level, line.strip())

    def flush(self):
        pass


class SuppressProgressLogs(logging.Filter):
    def filter(self, record):
        return "/progress/" not in record.getMessage()


def setup_user_logger(user_email):
    log_dir = os.path.join("output", user_email, "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_filename = datetime.now().strftime("reel_%Y%m%d_%H%M%S.log")
    log_path = os.path.join(log_dir, log_filename)

    root_logger = logging.getLogger()
    if not root_logger.hasHandlers():
        logging.basicConfig(
            level=logging.DEBUG,
            format='[%(asctime)s] %(levelname)s:%(name)s: %(message)s',
            handlers=[
                logging.FileHandler(log_path, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
    else:
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.addFilter(SuppressProgressLogs())
        stream_handler = logging.StreamHandler(sys.stdout)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(stream_handler)
        root_logger.setLevel(logging.DEBUG)

    sys.stdout = StreamToLogger(root_logger, logging.INFO)
    sys.stderr = StreamToLogger(root_logger, logging.ERROR)

    return log_path


logger = logging.getLogger("reel_job")
logger.setLevel(logging.DEBUG)


def schedule_reel(user_id: int, reel: Reel):
    from models.schedule import Schedule

    schedule_entry = Schedule(
        user_id=user_id,
        reel_id=reel.id,
        scheduled_for=None,
        timezone='Asia/Kolkata',
        status='pending'
    )
    db.session.add(schedule_entry)


def process_reel_job(
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
):
    from app import app

    with app.app_context():
        log_path = setup_user_logger(user_email)
        logger.info(f"🎬 Starting reel generation for {user_email} | Task ID: {task_id}")

        try:
            logger.info(f"[Reel Job] User ID: {user_id}, Email: {user_email}, Theme: {theme_name}")
            start_progress(task_id, user_id)

            user = db.session.query(User).filter_by(id=int(user_id)).first()
            if not user:
                finish_progress(task_id, "❌ User not found.", 0)
                return

            output_dir = os.path.join("output", user_email)
            scripts_dir = os.path.join(output_dir, "scripts")
            images_dir = os.path.join(output_dir, "images")
            tts_dir = os.path.join(output_dir, "tts")
            os.makedirs(scripts_dir, exist_ok=True)
            os.makedirs(images_dir, exist_ok=True)
            os.makedirs(tts_dir, exist_ok=True)

            update_progress(task_id, "📜 Saving script...", get_stage_percent(0))
            script_path = os.path.join(scripts_dir, f"{theme_name}_{language}_text.txt")
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(script_text)

            update_progress(task_id, "🖼️ Generating overlay...", get_stage_percent(1))
            text_image_path = os.path.join(images_dir, f"{theme_name}_{language}_text_image.png")
            generate_text_overlay(text_image_path, language, script_text)

            update_progress(task_id, "🔊 Processing voice...", get_stage_percent(2, 0.0))
            tts_filename = f"{theme_name}_{language}_voice.mp3"
            audio_path = os.path.join(tts_dir, tts_filename)

            if use_tts:
                audio_path, audio_duration = generate_tts_audio(
                    tts_path=audio_path,
                    language=language,
                    script_text=script_text,
                    tts_voice=voice,
                    cache=True
                )
            else:
                try:
                    result = subprocess.run([
                        "ffprobe", "-v", "error", "-show_entries",
                        "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
                        audio_path
                    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
                    audio_duration = float(result.stdout.strip())
                    logger.info(f"Audio duration: {audio_duration}s")
                    if result.stderr:
                        logger.error(result.stderr.strip())
                except subprocess.CalledProcessError as e:
                    logger.error("Error extracting audio duration with ffprobe")
                    logger.error(e.stderr)
                    finish_progress(task_id, "❌ Error extracting audio duration.", 0)
                    return

            if audio_duration < 2.0:
                finish_progress(task_id, "❌ Audio too short.", 0)
                return

            srt_path = ""
            if subtitles_enabled:
                update_progress(task_id, "📃 Generating subtitles...", get_stage_percent(3))
                srt_dir = os.path.join(output_dir, "srt")
                os.makedirs(srt_dir, exist_ok=True)
                srt_path = os.path.join(srt_dir, f"{theme_name}_{language}_srt.srt")
                generate_srt_from_audio(srt_path, language, audio_path, 6)

            update_progress(task_id, "🎶 Mixing background music...", get_stage_percent(4, 0.1))
            update_progress(task_id, "🎼 Translating script to English...", get_stage_percent(4, 0.2))
            english_script_text = translate_to_english(script_text)
            temp_dir = os.path.join(output_dir, "temp")
            os.makedirs(temp_dir, exist_ok=True)

            update_progress(task_id, "🎹 Fetching BGM...", get_stage_percent(4, 0.5))
            bgm_path = fetch_bgm(english_script_text, "en", "default") or "assets/music/default.mp3"

            update_progress(task_id, "🎧 Mixing BGM with voice...", get_stage_percent(4, 0.9))
            mixed_audio_path = os.path.join(temp_dir, f"{theme_name}_{language}_mixed.m4a")
            audio_to_use = audio_path

            if os.path.exists(bgm_path):
                try:
                    subprocess.run([
                        "ffmpeg", "-y", "-i", audio_path, "-i", bgm_path,
                        "-filter_complex", "[1:a]volume=0.1[a1];[0:a][a1]amix=inputs=2:duration=first:dropout_transition=2",
                        "-c:a", "aac", "-b:a", "192k", mixed_audio_path
                    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
                    audio_to_use = mixed_audio_path
                except subprocess.CalledProcessError as e:
                    logger.error("Error mixing audio:")
                    logger.error(e.stderr)

            update_progress(task_id, "🎞️ Fetching video clips...", get_stage_percent(5, 0.0))
            clips = fetch_multiple_clips(
                temp_dir, theme_name, language,
                english_script_text, audio_duration,
                task_id=task_id
            )

            if not clips:
                fallback_clips_dir = os.path.join("assets", "clips")
                clips = sorted([
                    os.path.join(fallback_clips_dir, f)
                    for f in os.listdir(fallback_clips_dir)
                    if f.lower().endswith((".mp4", ".mov", ".webm"))
                ])[:5]

            update_progress(task_id, f"🔗 Preparing to combine {len(clips)} clips...", get_stage_percent(5, 1.0))
            for idx, clip_path in enumerate(clips):
                update_progress(task_id, f"📥 Downloaded clip {idx + 1}/{len(clips)}", get_stage_percent(5, (idx + 1) / len(clips)))
                time.sleep(0.5)

            update_progress(task_id, "🎛️ Merging all clips...", get_stage_percent(6, 0.0))
            combined_video_path = concatenate_clips(
                temp_dir, theme_name, language, clips, task_id=task_id
            )

            if not combined_video_path:
                finish_progress(task_id, "❌ Video clips could not be combined.", 0)
                return

            update_progress(task_id, "🎬 Preparing final rendering filters...", get_stage_percent(7, 0.0))
            inputs = ["-i", combined_video_path, "-i", audio_to_use]
            input_index = 2
            logo_index = None

            if watermark_enabled:
                watermark_dir = os.path.join(output_dir, "watermark")
                os.makedirs(watermark_dir, exist_ok=True)
                watermark_path = os.path.join(watermark_dir, "logo.png")
                if not os.path.exists(watermark_path):
                    logger.warning("Custom logo not found, using default logo.")
                    watermark_path = os.path.join("assets", "logo", "default.png")
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
                filters.append(
                    f"[2:v][bg]scale2ref=w=iw/8:h=ow/mdar[logo][base_scaled];"
                    f"[base_scaled][logo]overlay=W-w-30:H-h-30[wm]"
                )
                base = "[wm]"

            map_video = base
            if subtitles_enabled and os.path.exists(srt_path):
                font_name = "NotoSansDevanagari-Regular" if language == "hi" else "DejaVuSans-Bold" if language == "en" else "Arial"
                style = (
                    f"Alignment=2,Fontname={font_name},Fontsize=16,"
                    "PrimaryColour=&H00FFFFFF,OutlineColour=&H80000000,"
                    "BorderStyle=3,Outline=2,MarginV=25"
                )
                escaped_srt = srt_path.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
                filters.append(f"{base}subtitles='{escaped_srt}':force_style='{style}'[outv]")
                map_video = "[outv]"

            videos_dir = os.path.join(output_dir, "videos")
            os.makedirs(videos_dir, exist_ok=True)
            video_path = os.path.join(videos_dir, f"{theme_name}_{language}_video.mp4")

            update_progress(task_id, "🎬 Generating final video...", get_stage_percent(7, 0.5))
            video_path = create_video(video_path, inputs, audio_duration, filters, map_video)
            if not video_path:
                finish_progress(task_id, "❌ Video could not be generated.", 0)
                return

            update_progress(task_id, "✅ Rendering complete!", get_stage_percent(7, 1.0))
            upload_url = None
            error = None

            if UPLOAD_TO_DRIVE:
                update_progress(task_id, "☁️ Uploading to Google Drive...", get_stage_percent(8, 0.5))
                upload_url, error = upload_to_google_drive(video_path, user_email)
                if upload_url:
                    logger.info(f"[✅] Uploaded to Google Drive: {upload_url}")
                elif error:
                    logger.error(f"[❌] Google Drive upload failed: {error}")

            if not upload_url:
                update_progress(task_id, "📂 Upload failed. Using local file path.", get_stage_percent(8, 0.9))
                filename = os.path.basename(video_path)
                upload_url = os.path.join("https://", HOST, "videos", user_email, filename).replace("\\", "/")
                logger.warning(f"[⚠️] Using fallback local video URL: {upload_url}")

            reel = Reel(
                user_id=user.id,
                title=theme_name.replace("_", " ").title(),
                script=script_text,
                caption=script_text,
                video_path=video_path,
                audio_path=audio_to_use,
                thumbnail_path=text_image_path,
                theme_name=theme_name,
                lang=language,
                status="draft"
            )
            db.session.add(reel)
            db.session.flush()

            try:
                schedule_reel(user_id=user.id, reel=reel)
                db.session.commit()
                finish_progress(task_id, "🎉 Reel is ready!", 100, download_url=upload_url)
                logger.info(f"✅ Reel generation complete and marked for scheduling. Log: {log_path}")
            except Exception as e:
                db.session.rollback()
                logger.error(f"Failed to schedule reel {reel.id if reel.id else '[unknown]'}: {e}")
                finish_progress(task_id, "✅ Reel created but scheduling failed.", 100, download_url=upload_url)

        except Exception as e:
            logger.exception("[Background Reel Task] Error:")
            db.session.rollback()
            finish_progress(task_id, "❌ Unexpected error during reel creation.", 0)

        finally:
            sys.stdout = ORIGINAL_STDOUT
            sys.stderr = ORIGINAL_STDERR

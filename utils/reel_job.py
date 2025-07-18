# File: utils/reel_job.py

import os
import subprocess
import logging
import sys
import time
from datetime import datetime
from utils.generate_text_overlay import generate_text_overlay
from utils.generate_tts_audio import generate_tts_audio
from utils.generate_srt_from_audio import generate_srt_from_audio
from utils.translate_text import translate_to_english
from utils.fetch_bgm import fetch_bgm
from utils.fetch_multiple_clips import fetch_multiple_clips, concatenate_clips
from utils.create_video import create_video
from utils.google_drive import upload_to_google_drive
from utils.reel_history import add_reel_to_history
from utils.progress_tracker import progress_status, start_progress, update_progress, finish_progress

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
        # Remove existing handlers and set new ones
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        stream_handler = logging.StreamHandler(sys.stdout)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(stream_handler)
        root_logger.setLevel(logging.DEBUG)

    # Redirect stdout and stderr
    sys.stdout = StreamToLogger(root_logger, logging.INFO)
    sys.stderr = StreamToLogger(root_logger, logging.ERROR)

    return log_path

logger = logging.getLogger("reel_job")
logger.setLevel(logging.DEBUG)

def generate_reel_background(
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
):
    log_path = setup_user_logger(user_email)
    logger.info(f"🎬 Starting reel generation for {user_email} | Task ID: {task_id}")

    try:
        start_progress(task_id)

        output_dir = os.path.join("output", user_email)
        scripts_dir = os.path.join(output_dir, "scripts")
        images_dir = os.path.join(output_dir, "images")
        tts_dir = os.path.join(output_dir, "tts")
        os.makedirs(scripts_dir, exist_ok=True)
        os.makedirs(images_dir, exist_ok=True)
        os.makedirs(tts_dir, exist_ok=True)

        update_progress(task_id, "📜 Saving script...", 5)
        script_filename = f"{theme_name}_{language}_text.txt"
        script_path = os.path.join(scripts_dir, script_filename)
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script_text)

        update_progress(task_id, "🖼️ Generating overlay...", 10)
        text_image_path = os.path.join(images_dir, f"{theme_name}_{language}_text_image.png")
        generate_text_overlay(text_image_path, language, script_text)

        update_progress(task_id, "🔊 Processing voice...", 20)
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
            audio_path = os.path.join(tts_dir, custom_voice_file.filename)
            custom_voice_file.save(audio_path)
            try:
                result = subprocess.run([
                    "ffprobe", "-v", "error", "-show_entries",
                    "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
                    audio_path
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
                audio_duration = float(result.stdout.strip())
                logger.info(result.stdout.strip())
                if result.stderr:
                    logger.error(result.stderr.strip())
            except subprocess.CalledProcessError as e:
                logger.error("Error extracting audio duration with ffprobe")
                logger.error(e.stderr)
                raise

        if audio_duration < 2.0:
            finish_progress(task_id, "❌ Audio too short.", 0)
            return

        srt_path = ""
        if subtitles_enabled:
            update_progress(task_id, "📃 Generating subtitles...", 30)
            srt_dir = os.path.join(output_dir, "srt")
            os.makedirs(srt_dir, exist_ok=True)
            srt_filename = f"{theme_name}_{language}_srt.srt"
            srt_path = os.path.join(srt_dir, srt_filename)
            generate_srt_from_audio(srt_path, language, audio_path, 6)

        update_progress(task_id, "🎶 Mixing background music...", 40)
        update_progress(task_id, "🎼 Translating script to English...", 41)
        english_script_text = translate_to_english(script_text)
        temp_dir = os.path.join(output_dir, "temp")
        os.makedirs(temp_dir, exist_ok=True)

        update_progress(task_id, "🎹 Fetching BGM...", 42)
        bgm_path = fetch_bgm(english_script_text, "en", "default") or "assets/music/default.mp3"

        update_progress(task_id, "🎧 Mixing BGM with voice...", 45)
        mixed_audio_path = os.path.join(temp_dir, f"{theme_name}_{language}_mixed.m4a")
        audio_to_use = audio_path

        if os.path.exists(bgm_path):
            try:
                result = subprocess.run([
                    "ffmpeg", "-y", "-i", audio_path, "-i", bgm_path,
                    "-filter_complex", "[1:a]volume=0.1[a1];[0:a][a1]amix=inputs=2:duration=first:dropout_transition=2",
                    "-c:a", "aac", "-b:a", "192k", mixed_audio_path
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
                logger.info(result.stdout)
                if result.stderr:
                    logger.error(result.stderr.strip())
                audio_to_use = mixed_audio_path
            except subprocess.CalledProcessError as e:
                logger.error("Error mixing audio:")
                logger.error(e.stderr)

        update_progress(task_id, "🎞️ Fetching video clips...", 55)
        clips = fetch_multiple_clips(
            temp_dir, theme_name, language,
            english_script_text, audio_duration,
            task_id=task_id,
            start_percent=55,
            end_percent=65
        )

        if not clips:
            fallback_clips_dir = os.path.join("assets", "clips")
            clips = sorted([
                os.path.join(fallback_clips_dir, f)
                for f in os.listdir(fallback_clips_dir)
                if f.lower().endswith((".mp4", ".mov", ".webm"))
            ])[:5]

        update_progress(task_id, f"🔗 Preparing to combine {len(clips)} clips...", 65)

        for idx, clip_path in enumerate(clips):
            percent = 65 + int((idx + 1) / len(clips) * 5)
            update_progress(task_id, f"📥 Downloaded clip {idx + 1}/{len(clips)}", percent)
            time.sleep(0.5)

        update_progress(task_id, "🎛️ Merging all clips...", 70)
        combined_video_path = concatenate_clips(
            temp_dir, theme_name, language, clips,
            task_id=task_id,
            start_percent=70,
            end_percent=80
        )

        if not combined_video_path:
            finish_progress(task_id, "❌ Video clips could not be combined.", 0)
            return

        update_progress(task_id, "🎬 Preparing final rendering filters...", 80)
        inputs = ["-i", combined_video_path, "-i", audio_to_use]
        input_index = 2
        logo_index = None

        if watermark_enabled:
            watermark_dir = os.path.join(output_dir, "watermark")
            os.makedirs(watermark_dir, exist_ok=True)
            watermark_path = os.path.join(watermark_dir, "logo.png")
            if not os.path.exists(watermark_path):
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
            filters.append(f"{base}[{logo_index}:v]overlay=W-w-30:H-h-30[wm]")
            base = "[wm]"

        if subtitles_enabled and os.path.exists(srt_path):
            style = (
                "Alignment=2,Fontname=DejaVuSans-Bold,Fontsize=16,"
                "PrimaryColour=&H00FFFFFF,OutlineColour=&H80000000,"
                "BorderStyle=3,Outline=2,MarginV=10"
            )
            escaped_srt = srt_path.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
            filters.append(f"{base}subtitles='{escaped_srt}':force_style='{style}'[outv]")
            map_video = "[outv]"
        else:
            map_video = base

        videos_dir = os.path.join(output_dir, "videos")
        os.makedirs(videos_dir, exist_ok=True)
        video_path = os.path.join(videos_dir, f"{theme_name}_{language}_video.mp4")

        update_progress(task_id, "🎬 Generating final video with FFmpeg...", 82)
        video_path = create_video(video_path, inputs, audio_duration, filters, map_video)
        if not video_path:
            finish_progress(task_id, "❌ Video could not be generated.", 0)
            return

        update_progress(task_id, "✅ Rendering complete!", 89)
        update_progress(task_id, "☁️ Uploading to Google Drive...", 95)
        upload_url, error = upload_to_google_drive(video_path, user_email)
        if error:
            finish_progress(task_id, error, 0)
            return

        add_reel_to_history(user_email, os.path.basename(video_path), script_text)
        finish_progress(task_id, "✅ Reel created!", 100)
        progress_status[task_id]["download_url"] = upload_url
        logger.info(f"✅ Reel generation complete. Log: {log_path}")

    except Exception as e:
        logger.exception("[Background Reel Task] Error:")
        finish_progress(task_id, "❌ Unexpected error during reel creation.", 0)

    finally:
        sys.stdout = ORIGINAL_STDOUT
        sys.stderr = ORIGINAL_STDERR

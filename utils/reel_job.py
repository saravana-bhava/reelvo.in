# File: utils/reel_job.py

import os
import subprocess
import logging
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

logger = logging.getLogger("reel_job")

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
            audio_duration = float(subprocess.check_output([
                "ffprobe", "-v", "error", "-show_entries",
                "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
                audio_path
            ]).decode().strip())

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
        english_script_text = translate_to_english(script_text)
        temp_dir = os.path.join(output_dir, "temp")
        os.makedirs(temp_dir, exist_ok=True)

        bgm_path = fetch_bgm(english_script_text, "en", "default") or "assets/music/default.mp3"
        mixed_audio_path = os.path.join(temp_dir, f"{theme_name}_{language}_mixed.m4a")
        audio_to_use = audio_path

        if os.path.exists(bgm_path):
            subprocess.run([
                "ffmpeg", "-y", "-i", audio_path, "-i", bgm_path,
                "-filter_complex", "[1:a]volume=0.1[a1];[0:a][a1]amix=inputs=2:duration=first:dropout_transition=2",
                "-c:a", "aac", "-b:a", "192k", mixed_audio_path
            ], check=True)
            audio_to_use = mixed_audio_path

        update_progress(task_id, "🎞️ Fetching video clips...", 55)
        clips = fetch_multiple_clips(temp_dir, theme_name, language, english_script_text, audio_duration)
        if not clips:
            fallback_clips_dir = os.path.join("assets", "clips")
            clips = sorted([
                os.path.join(fallback_clips_dir, f)
                for f in os.listdir(fallback_clips_dir)
                if f.lower().endswith((".mp4", ".mov", ".webm"))
            ])[:5]

        update_progress(task_id, f"🔗 Preparing to combine {len(clips)} clips...", 65)

        # Simulate progress as each clip is prepared (optional)
        for idx, clip_path in enumerate(clips):
            percent = 65 + int((idx + 1) / len(clips) * 5)
            update_progress(task_id, f"🧩 Queuing clip {idx + 1} of {len(clips)}...", percent)

        update_progress(task_id, "🎛️ Merging all clips...", 70)
        combined_video_path = concatenate_clips(temp_dir, theme_name, language, clips)

        if not combined_video_path:
            finish_progress(task_id, "❌ Video clips could not be combined.", 0)
            return

        update_progress(task_id, "🎬 Rendering final reel...", 80)
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

        video_path = create_video(video_path, inputs, audio_duration, filters, map_video)
        if not video_path:
            finish_progress(task_id, "❌ Video could not be generated.", 0)
            return

        update_progress(task_id, "☁️ Uploading to Google Drive...", 95)
        upload_url = upload_to_google_drive(video_path, user_email)
        add_reel_to_history(user_email, os.path.basename(video_path), script_text)

        finish_progress(task_id, "✅ Reel created!", 100)
        progress_status[task_id]["download_url"] = upload_url


    except Exception as e:
        logger.exception("[Background Reel Task] Error:")
        finish_progress(task_id, "❌ Unexpected error during reel creation.", 0)

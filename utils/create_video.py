# File: create_video.py

"""
Generates a full Instagram Reel from a script:
5. Background music mix
6. Watermark (optional)
7. Output high-quality 1080x1920 MP4
"""

import logging
import os
import re
import subprocess
import srt
import sys
from datetime import timedelta
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(ROOT_DIR, ".env"))

from utils.generate_script import generate_script_for_user
from utils.pixabay_video import fetch_pixabay_video
from utils.pexels_video import fetch_pexels_video
from utils.video_utils import download_video
from utils.fetch_bgm import fetch_bgm
from utils.progress_tracker import start_progress, update_progress, finish_progress
from utils.translate_text import translate_to_english

# Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("create_video")

# Constants
IMAGE_DIR = "assets/images"
VIDEO_DIR = "assets/videos"
TEMP_DIR = "temp"
WATERMARK_PATH = "assets/logo.png"
DEFAULT_BGM_PATH = "assets/bgm.mp3"
CLIP_DURATION = 5.5

USE_PIXABAY = os.getenv("USE_PIXABAY", "true").lower() == "true"
USE_PEXELS = os.getenv("USE_PEXELS", "false").lower() == "true"


def clip_srt_timing(srt_path, start=0.5, end=29.5):
    with open(srt_path, 'r', encoding='utf-8') as f:
        subs = list(srt.parse(f.read()))
    clipped = []
    for sub in subs:
        s = max(sub.start.total_seconds(), start)
        e = min(sub.end.total_seconds(), end)
        if s < e:
            sub.start = timedelta(seconds=s)
            sub.end = timedelta(seconds=e)
            clipped.append(sub)
    with open(srt_path, 'w', encoding='utf-8') as f:
        f.write(srt.compose(clipped))


def sanitize_english(text: str) -> str:
    words = re.findall(r'\b\w+\b', text.lower())
    ascii_words = [w for w in words if w.isascii()]
    return " ".join(ascii_words) or "inspiration"


def fetch_multiple_clips(script_text, target_duration, fallback_theme):
    count = int(target_duration / CLIP_DURATION) + 1
    downloaded_clips = []
    used_urls = set()
    sources = []
    if USE_PEXELS:
        sources.append(fetch_pexels_video)
    if USE_PIXABAY:
        sources.append(fetch_pixabay_video)

    fallback_local = os.path.join(VIDEO_DIR, f"{fallback_theme}.mp4")
    search_query = sanitize_english(script_text)

    for i in range(count):
        clip_path = os.path.join(TEMP_DIR, f"{fallback_theme}_clip{i+1}.mp4")
        found = False
        for source in sources:
            url = source(search_query, clip_path, used_urls=used_urls)
            if url:
                used_urls.add(url)
                downloaded_clips.append(clip_path)
                found = True
                break
        if not found and os.path.exists(fallback_local):
            if download_video(fallback_local, clip_path, min_duration=5, max_duration=6):
                downloaded_clips.append(clip_path)

    return downloaded_clips


def concatenate_clips(clips, output_path):
    logger.info("[🔁] Re-encoding and concatenating clips...")
    reencoded_clips = []
    for i, clip in enumerate(clips):
        fixed = os.path.join(TEMP_DIR, f"fixed_clip{i+1}.mp4")
        subprocess.run([
            "ffmpeg", "-y", "-i", clip,
            "-vf", "scale=1080:1920,fps=30",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-c:a", "aac", "-ac", "2", "-b:a", "128k",
            "-movflags", "+faststart",
            fixed
        ], check=True)
        reencoded_clips.append(fixed)

    list_file = os.path.join(TEMP_DIR, "concat_list.txt")
    with open(list_file, "w") as f:
        for clip in reencoded_clips:
            f.write(f"file '{os.path.abspath(clip)}'\n")

    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file,
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        output_path
    ], check=True)

    return output_path


def create_video_for_theme(
    theme,
    user_name,
    include_watermark=True,
    bgm_path=None,
    language="en",
    task_id=None,
    script_text=None,
    voiceover_path=None,
    tts_voice=None,
    include_subtitles=True
):
    logger.info(f"🎬 Starting reel for: {theme.upper()} | User: {user_name} | Lang: {language}")
    os.makedirs("output", exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)
    base_output = os.path.join("output", user_name)
    os.makedirs(base_output, exist_ok=True)

    if task_id:
        start_progress(task_id)

    if not script_text:
        text_path = generate_script_for_user(theme, user_name, language=language)
        with open(text_path, "r", encoding="utf-8") as f:
            script_text = f.read().strip()

    audio_path = os.path.join(base_output, "tts", f"{theme}_{language}_tts.mp3")
    text_image_path = os.path.join(base_output, "image", f"{theme}_{language}_image.png")
    srt_path = os.path.join(base_output, "srt", f"{theme}_{language}_srt.srt")
    final_output_path = os.path.join(base_output, "video", f"{theme}_{language}_video.mp4")

    if task_id: update_progress(task_id, "🎞️ Fetching video clips...", 60)

    english_script = translate_to_english(script_text)
    clips = fetch_multiple_clips(english_script, audio_duration, fallback_theme=theme)
    if not clips:
        logger.error("[❌] No video clips found.")
        return None

    if task_id: update_progress(task_id, "🎬 Concatenating clips...", 70)
    combined_video_path = os.path.join(TEMP_DIR, f"{theme}_combined.mp4")
    concatenate_clips(clips, combined_video_path)

    # Audio mixing
    mixed_audio_path = os.path.join(TEMP_DIR, f"{theme}_{language}_mixed.m4a")
    if not bgm_path or not os.path.exists(bgm_path):
        try:
            bgm_path = fetch_bgm(english_script, "en", "default") or DEFAULT_BGM_PATH
        except Exception:
            bgm_path = None

    audio_to_use = audio_path
    if bgm_path and os.path.exists(bgm_path):
        subprocess.run([
            "ffmpeg", "-y", "-i", audio_path, "-i", bgm_path,
            "-filter_complex", "[1:a]volume=0.1[a1];[0:a][a1]amix=inputs=2:duration=first:dropout_transition=2",
            "-c:a", "aac", "-b:a", "192k", mixed_audio_path
        ], check=True)
        audio_to_use = mixed_audio_path

    # Final render
    inputs = ["-i", combined_video_path, "-i", audio_to_use]
    input_index = 2
    logo_index = None

    if include_watermark and os.path.exists(WATERMARK_PATH):
        inputs += ["-loop", "1", "-t", str(audio_duration), "-i", WATERMARK_PATH]
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

    if include_subtitles:
        subtitle_style = (
            "Alignment=2,Fontname=DejaVuSans-Bold,Fontsize=16,"
            "PrimaryColour=&H00FFFFFF,OutlineColour=&H80000000,"
            "BorderStyle=3,Outline=2,MarginV=10"
        )
        filters.append(f"{base}subtitles='{srt_path}':force_style='{subtitle_style}'[outv]")
        map_video = "[outv]"
    else:
        map_video = base

    cmd = [
        "ffmpeg", *inputs,
        "-t", str(audio_duration),
        "-filter_complex", ";".join(filters),
        "-map", map_video, "-map", "1:a",
        "-c:v", "libx264", "-preset", "slow", "-crf", "18",
        "-b:v", "10M", "-minrate", "8M", "-maxrate", "12M", "-bufsize", "12M",
        "-c:a", "aac", "-ar", "44100", "-b:a", "256k", "-ac", "2",
        "-movflags", "+faststart", "-pix_fmt", "yuv420p", "-r", "30",
        "-y", final_output_path
    ]

    try:
        logger.info(f"[📦] Final FFmpeg render command:\n{' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        if task_id: finish_progress(task_id, "✅ Video generated!")
        logger.info(f"[✅] Reel created: {final_output_path}")
        return final_output_path
    except subprocess.CalledProcessError:
        logger.exception("[❌] FFmpeg final render failed")
        return None


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 3:
        theme, user_name = sys.argv[1], sys.argv[2]
        include_watermark = sys.argv[3].lower() == "true" if len(sys.argv) >= 4 else True
        bgm_path = sys.argv[4] if len(sys.argv) >= 5 else None
        language = sys.argv[5] if len(sys.argv) >= 6 else "en"
        create_video_for_theme(
            theme, user_name, include_watermark=include_watermark,
            bgm_path=bgm_path, language=language
        )
    else:
        print("Usage: python create_video.py <theme> <user_name> [include_watermark=True] [bgm_path] [language=en]")

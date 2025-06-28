# create_video.py

import os
import subprocess
import logging
from datetime import timedelta
import srt
from dotenv import load_dotenv

from utils.gen_text_overlay import generate_text_overlay
from utils.gen_tts_audio import generate_tts_from_file
from utils.gen_subtitles import generate_srt_from_audio
from utils.generate_script import generate_script_for_user
from utils.pixabay_video import fetch_pixabay_video
from utils.pexels_video import try_pexels_fallback
from utils.video_utils import download_video, get_video_duration

load_dotenv()

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("create_video")

# Constants
IMAGE_DIR = "assets/images"
VIDEO_DIR = "assets/videos"
TEMP_DIR = "temp"
WATERMARK_PATH = "assets/logo.png"
VIDEO_DURATION = 30
CLIP_COUNT = 5
CATEGORIES = ["motivation", "success", "life", "inspiration", "sad"]

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

def fetch_multiple_clips(category, count=5):
    downloaded_clips = []
    used_urls = set()
    sources = [try_pexels_fallback, fetch_pixabay_video]
    fallback_local = os.path.join(VIDEO_DIR, f"{category}.mp4")

    for i in range(count):
        clip_path = os.path.join(TEMP_DIR, f"{category}_clip{i+1}.mp4")
        for source in sources:
            if source == try_pexels_fallback and USE_PEXELS:
                if try_pexels_fallback(category, clip_path, used_urls=used_urls):
                    downloaded_clips.append(clip_path)
                    break
            elif source == fetch_pixabay_video and USE_PIXABAY:
                if fetch_pixabay_video(category, clip_path, used_urls=used_urls):
                    downloaded_clips.append(clip_path)
                    break
        else:
            if os.path.exists(fallback_local):
                downloaded = download_video(fallback_local, clip_path, min_duration=5, max_duration=6)
                if downloaded:
                    downloaded_clips.append(clip_path)

    return downloaded_clips

def concatenate_clips(clips, output_path):
    logger.info("[🔁] Re-encoding clips for safe concatenation...")
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

def create_video_for_category(category, username):
    logger.info(f"🎬 Generating reel for: {category.upper()} | User: {username}")
    os.makedirs("output", exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)

    base_output = os.path.join("output", username)
    os.makedirs(base_output, exist_ok=True)

    text_path = generate_script_for_user(category, username)
    if not os.path.exists(text_path):
        logger.error(f"[❌] Failed to generate script for {category}")
        return None

    audio_path = os.path.join(base_output, f"{category}.mp3")
    text_image_path = os.path.join(base_output, f"{category}_text.png")
    srt_path = os.path.join(base_output, f"{category}.srt")
    final_output_path = os.path.join(base_output, f"{category}.mp4")

    with open(text_path, "r", encoding="utf-8") as f:
        script = f.read().strip()

    try:
        generate_text_overlay(script, text_image_path)
        audio_path = generate_tts_from_file(category, username)
        generate_srt_from_audio(category, audio_path, srt_path)
    except Exception as e:
        logger.exception("[❌] Asset generation failed")
        return None

    clip_srt_timing(srt_path, 0.5, 29.5)

    clips = fetch_multiple_clips(category, CLIP_COUNT)
    if not clips:
        logger.error("[❌] No background clips found.")
        return None

    combined_video_path = os.path.join(TEMP_DIR, f"{category}_combined.mp4")
    concatenate_clips(clips, combined_video_path)

    inputs = ["-i", combined_video_path, "-i", audio_path]
    input_index = 2

    logo_index = None
    if os.path.exists(WATERMARK_PATH):
        inputs += ["-loop", "1", "-t", str(VIDEO_DURATION), "-i", WATERMARK_PATH]
        logo_index = input_index
        input_index += 1

    filters = [
        f"[0:v]scale=1080:1920:force_original_aspect_ratio=decrease,"
        f"pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1,"
        f"fade=t=in:st=0:d=1,fade=t=out:st={VIDEO_DURATION-1}:d=1[bg]"
    ]

    base_stream = "[bg]"

    if logo_index is not None:
        filters.append(f"{base_stream}[{logo_index}:v]overlay=W-w-30:H-h-30[wm]")
        base_stream = "[wm]"

    subtitle_style = (
        "Alignment=2,"  # Bottom center
        "Fontname=DejaVuSans-Bold,"
        "Fontsize=16,"  # Smaller size for readability
        "PrimaryColour=&H00FFFFFF,"  # White
        "OutlineColour=&H80000000,"  # Semi-transparent black border
        "BorderStyle=3,"  # Opaque box
        "Outline=2,"  # Thin border
        "MarginV=100"  # Push above bottom bar
    )

    filters.append(f"{base_stream}subtitles='{srt_path}':force_style='{subtitle_style}'[outv]")

    cmd = [
        "ffmpeg", *inputs,
        "-filter_complex", ";".join(filters),
        "-map", "[outv]",
        "-map", "1:a",
        "-c:v", "libx264", "-preset", "slow", "-crf", "18",
        "-b:v", "10M", "-minrate", "8M", "-maxrate", "12M", "-bufsize", "12M",
        "-c:a", "aac", "-ar", "44100", "-b:a", "256k", "-ac", "2",
        "-movflags", "+faststart",
        "-pix_fmt", "yuv420p",
        "-r", "30",
        "-y", final_output_path
    ]

    logger.info(f"[📦] Running FFmpeg command:\n{' '.join(cmd)}")

    try:
        subprocess.run(cmd, check=True)
        logger.info(f"[✅] Final reel generated: {final_output_path}")
        return final_output_path
    except subprocess.CalledProcessError as e:
        logger.exception("[❌] FFmpeg failed")
        return None


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 3:
        category, username = sys.argv[1], sys.argv[2]
        create_video_for_category(category, username)
    else:
        print("Usage: python create_video.py <category> <username>")

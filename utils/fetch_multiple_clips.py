# File: utils/fetch_multiple_clips.py

import os
import re
import logging
import subprocess
from utils.pixabay_video import fetch_pixabay_video
from utils.pexels_video import fetch_pexels_video
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
CLIP_DURATION = 5.5
DISABLE_CACHE = os.getenv("DISABLE_CACHE", "false").lower() == "true"
USE_PEXELS = os.getenv("USE_PEXELS", "false").lower() == "true"
USE_PIXABAY = os.getenv("USE_PIXABAY", "true").lower() == "true"

# Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("download_clips")

def sanitize_english(text: str) -> str:
    words = re.findall(r'\b\w+\b', text.lower())
    ascii_words = [w for w in words if w.isascii()]
    return " ".join(ascii_words) or "inspiration"


def fetch_multiple_clips(
    user_name: str,
    folder_name: str,
    theme_name: str,
    language: str,
    script_text: str,
    target_duration
):
    logger.info(f"🎞️ Fetching video clips...")
    count = int(target_duration / CLIP_DURATION) + 1
    downloaded_clips = []
    used_urls = set()
    sources = []
    if USE_PEXELS:
        sources.append(fetch_pexels_video)
    if USE_PIXABAY:
        sources.append(fetch_pixabay_video)

    fallback_local = os.path.join("assets", "videos", f"{theme_name}.mp4")
    search_query = sanitize_english(script_text)

    for i in range(count):
        clip_path = os.path.join("output", user_name, folder_name, f"{theme_name}_{language}_clip{i+1}.mp4")
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


def concatenate_clips(
    user_name: str,
    folder_name: str,
    theme_name: str,
    language: str,
    clips
):
    logger.info("[🔁] Re-encoding and concatenating clips...")
    reencoded_clips = []
    for i, clip in enumerate(clips):
        fixed = os.path.join("output", user_name, folder_name, f"{theme_name}_{language}_fixed_clip{i+1}.mp4")
        subprocess.run([
            "ffmpeg", "-y", "-i", clip,
            "-vf", "scale=1080:1920,fps=30",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-c:a", "aac", "-ac", "2", "-b:a", "128k",
            "-movflags", "+faststart",
            fixed
        ], check=True)
        reencoded_clips.append(fixed)

    list_file = os.path.join("output", "temp", "concat_list.txt")
    with open(list_file, "w") as f:
        for clip in reencoded_clips:
            f.write(f"file '{os.path.abspath(clip)}'\n")

    combined_video_path = os.path.join("output", user_name, folder_name, f"{theme_name}_{language}_combined.mp4")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file,
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        combined_video_path
    ], check=True)

    return combined_video_path

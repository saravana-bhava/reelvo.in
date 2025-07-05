# File: utils/fetch_multiple_clips.py

import os
import re
import logging
import subprocess
from typing import List
from dotenv import load_dotenv
from utils.pixabay_video import fetch_pixabay_video
from utils.pexels_video import fetch_pexels_video

# Load environment variables
load_dotenv()

CLIP_DURATION = 5.5
DISABLE_CACHE = os.getenv("DISABLE_CACHE", "false").lower() == "true"
USE_PEXELS = os.getenv("USE_PEXELS", "false").lower() == "true"
USE_PIXABAY = os.getenv("USE_PIXABAY", "true").lower() == "true"

# Logger setup
logger = logging.getLogger("download_clips")
logging.basicConfig(level=logging.INFO)


def sanitize_english(text: str) -> str:
    """Extract English words from input text for search query."""
    words = re.findall(r'\b\w+\b', text.lower())
    ascii_words = [w for w in words if w.isascii()]
    return " ".join(ascii_words) or "inspiration"


def download_video(src_path: str, dest_path: str, min_duration=5, max_duration=6) -> bool:
    """Trim a local video clip from a source file and save to destination."""
    try:
        subprocess.run([
            "ffmpeg", "-y", "-i", src_path,
            "-ss", "0", "-t", str(max_duration),
            "-vf", "scale=1080:1920,fps=30",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-c:a", "aac", "-ac", "2", "-b:a", "128k",
            "-movflags", "+faststart",
            dest_path
        ], check=True)
        return True
    except Exception as e:
        logger.error(f"[❌] Failed to copy fallback clip '{src_path}' to '{dest_path}': {e}")
        return False


def fetch_multiple_clips(
    temp_dir: str,
    theme_name: str,
    language: str,
    script_text: str,
    target_duration: float
) -> List[str]:
    """
    Download multiple clips from Pixabay or Pexels for the given script.
    Falls back to local assets if APIs fail.
    """
    logger.info("🎞️ Fetching video clips...")

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

    os.makedirs(temp_dir, exist_ok=True)

    for i in range(count):
        clip_path = os.path.join(temp_dir, f"{theme_name}_{language}_clip{i+1}.mp4")
        found = False

        for source in sources:
            try:
                url = source(search_query, clip_path, used_urls=used_urls)
                if url:
                    used_urls.add(url)
                    downloaded_clips.append(clip_path)
                    found = True
                    break
            except Exception as e:
                logger.warning(f"[⚠️] Source error: {source.__name__} failed: {e}")

        if not found and os.path.exists(fallback_local):
            if download_video(fallback_local, clip_path):
                downloaded_clips.append(clip_path)
                found = True

        if not found:
            logger.warning(f"[⚠️] Clip {i+1} could not be downloaded from any source.")

    return downloaded_clips


def concatenate_clips(
    temp_dir: str,
    theme_name: str,
    language: str,
    clips: List[str]
) -> str:
    """Re-encode and concatenate video clips into a single vertical video."""
    logger.info("[🔁] Re-encoding and concatenating clips...")

    reencoded_clips = []

    for i, clip in enumerate(clips):
        fixed = os.path.join(temp_dir, f"{theme_name}_{language}_fixed_clip{i+1}.mp4")
        try:
            subprocess.run([
                "ffmpeg", "-y", "-i", clip,
                "-vf", "scale=1080:1920,fps=30",
                "-c:v", "libx264", "-preset", "fast", "-crf", "20",
                "-c:a", "aac", "-ac", "2", "-b:a", "128k",
                "-movflags", "+faststart",
                fixed
            ], check=True)
            reencoded_clips.append(fixed)
        except Exception as e:
            logger.error(f"[❌] Failed to re-encode {clip}: {e}")

    if not reencoded_clips:
        raise RuntimeError("[❌] No valid clips to concatenate.")

    list_file = os.path.join(temp_dir, "concat_list.txt")
    with open(list_file, "w") as f:
        for clip in reencoded_clips:
            f.write(f"file '{os.path.abspath(clip)}'\n")

    combined_video_path = os.path.join(temp_dir, f"{theme_name}_{language}_combined.mp4")
    try:
        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file,
            "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart",
            combined_video_path
        ], check=True)
    except Exception as e:
        raise RuntimeError(f"[❌] Failed to concatenate clips: {e}")

    return combined_video_path

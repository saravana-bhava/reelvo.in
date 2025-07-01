# File: utils/video_utils.py

"""
Handles video downloading, caching, trimming, and duration validation.
Supports Instagram Reels standards: portrait 1080x1920, duration 5–6s per clip.
"""

import os
import subprocess
import requests
import hashlib
import shutil
import logging
from typing import Optional, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DISABLE_CACHE = os.getenv("DISABLE_CACHE", "false").lower() == "true"

# Logging setup
logger = logging.getLogger("video_utils")
logging.basicConfig(level=logging.INFO)

# Constants
CACHE_DIR = os.path.join("cache", "videos")
os.makedirs(CACHE_DIR, exist_ok=True)


def get_video_duration(filepath: str) -> Optional[float]:
    """Returns video duration in seconds using ffprobe."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                filepath
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        return float(result.stdout.strip())
    except Exception as e:
        logger.warning(f"[❌] ffprobe failed: {e}")
        return None


def trim_video(input_path: str, output_path: str, max_duration: int = 30) -> bool:
    """
    Trims a video to the specified duration using FFmpeg.

    Args:
        input_path: Source file.
        output_path: Trimmed file path.
        max_duration: Max duration in seconds.

    Returns:
        bool: True if success, else False.
    """
    try:
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", input_path,
                "-t", str(max_duration),
                "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                "-c:a", "aac", "-b:a", "128k",
                output_path
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT
        )
        logger.info(f"[✂️] Trimmed video to {max_duration}s → {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"[❌] FFmpeg trim error: {e}")
        return False


def download_video(
    url: str,
    output_path: str,
    min_duration: int = 5,
    max_duration: int = 6,
    return_url: bool = False
) -> str | Tuple[Optional[str], Optional[str]]:
    """
    Downloads a video, validates/trims duration, and caches it.

    Args:
        url: Source URL.
        output_path: Target local path.
        min_duration: Minimum allowed duration.
        max_duration: Maximum allowed duration.
        return_url: If True, returns (output_path, url), else just output_path.

    Returns:
        str or tuple: Final path (or path, url) if valid, else None.
    """
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        hashed = hashlib.md5(url.encode()).hexdigest()
        cached_path = os.path.join(CACHE_DIR, f"{hashed}.mp4")

        # Use cached file if valid
        if not DISABLE_CACHE and os.path.exists(cached_path):
            logger.info(f"[📦] Using cached video for: {url}")
            duration = get_video_duration(cached_path)
            if duration and duration >= min_duration:
                shutil.copyfile(cached_path, output_path)
                return (output_path, url) if return_url else output_path
            logger.warning("[⚠️] Cached video invalid or too short. Deleting...")
            os.remove(cached_path)

        # Download video to temp path
        logger.info(f"[⬇️] Downloading from: {url}")
        temp_path = output_path + ".tmp"
        with requests.get(url, stream=True, timeout=15) as r:
            r.raise_for_status()
            with open(temp_path, "wb") as f:
                for chunk in r.iter_content(1024 * 1024):
                    f.write(chunk)

        duration = get_video_duration(temp_path)
        if duration is None:
            logger.warning("[⚠️] Could not get duration. Saving as-is.")
            os.rename(temp_path, output_path)
            if not DISABLE_CACHE:
                shutil.copyfile(output_path, cached_path)
            return (output_path, url) if return_url else output_path

        if duration < min_duration:
            logger.warning(f"[⏹️] Skipping: too short ({duration:.2f}s < {min_duration}s)")
            os.remove(temp_path)
            return (None, None) if return_url else None

        if duration > max_duration:
            logger.info(f"[⏱️] Trimming: {duration:.2f}s → {max_duration}s")
            success = trim_video(temp_path, output_path, max_duration)
            os.remove(temp_path)
            if success and not DISABLE_CACHE:
                shutil.copyfile(output_path, cached_path)
            return (output_path, url) if return_url else (output_path if success else None)

        # Finalize video (valid duration)
        os.rename(temp_path, output_path)
        logger.info(f"[✅] Downloaded OK ({duration:.2f}s) → {output_path}")
        if not DISABLE_CACHE:
            shutil.copyfile(output_path, cached_path)

        return (output_path, url) if return_url else output_path

    except Exception as e:
        logger.error(f"[❌] Video download error: {e}")
        return (None, None) if return_url else None

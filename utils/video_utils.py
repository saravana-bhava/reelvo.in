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
    """Get duration of a video file using ffprobe."""
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


def trim_video(input_path: str, output_path: str, max_duration: int = 6) -> bool:
    """
    Trim video to max_duration using FFmpeg.

    Args:
        input_path: Path to original video.
        output_path: Path for trimmed video.
        max_duration: Duration in seconds to trim to (default 6).
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
        logger.info(f"[✂️] Trimmed to {max_duration}s → {output_path}")
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
    Download video from URL, validate duration, optionally trim and cache.

    Args:
        url: Video source URL.
        output_path: Path to save the downloaded video.
        min_duration: Minimum acceptable duration in seconds.
        max_duration: Maximum duration allowed (clips trimmed to this).
        return_url: If True, returns (path, url) tuple else just path.

    Returns:
        str | tuple: Output path (or path, url), or None on failure.
    """
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        hashed = hashlib.md5(url.encode()).hexdigest()
        cached_path = os.path.join(CACHE_DIR, f"{hashed}.mp4")

        if not DISABLE_CACHE and os.path.exists(cached_path):
            logger.info(f"[📦] Using cached version for: {url}")
            duration = get_video_duration(cached_path)
            if duration and duration >= min_duration:
                shutil.copyfile(cached_path, output_path)
                return (output_path, url) if return_url else output_path
            logger.warning("[⚠️] Cached video too short. Removing...")
            os.remove(cached_path)

        logger.info(f"[⬇️] Downloading from: {url}")
        temp_path = output_path + ".tmp"
        with requests.get(url, stream=True, timeout=15) as r:
            r.raise_for_status()
            with open(temp_path, "wb") as f:
                for chunk in r.iter_content(1024 * 1024):
                    f.write(chunk)
            # file is flushed and closed automatically here

        duration = get_video_duration(temp_path)
        if duration is None:
            logger.warning("[⚠️] No duration detected. Saving as-is.")
            os.replace(temp_path, output_path)
            if not DISABLE_CACHE:
                shutil.copyfile(output_path, cached_path)
            return (output_path, url) if return_url else output_path

        if duration < min_duration:
            logger.warning(f"[⏹️] Too short: {duration:.2f}s < {min_duration}s")
            os.remove(temp_path)
            return (None, None) if return_url else None

        if duration > max_duration:
            logger.info(f"[⏱️] Trimming: {duration:.2f}s → {max_duration}s")
            success = trim_video(temp_path, output_path, max_duration)
            os.remove(temp_path)
            if success and not DISABLE_CACHE:
                shutil.copyfile(output_path, cached_path)
            return (output_path, url) if return_url else (output_path if success else None)

        os.replace(temp_path, output_path)
        logger.info(f"[✅] Downloaded OK ({duration:.2f}s) → {output_path}")
        if not DISABLE_CACHE:
            shutil.copyfile(output_path, cached_path)

        return (output_path, url) if return_url else output_path

    except Exception as e:
        logger.error(f"[❌] Download error: {e}")
        return (None, None) if return_url else None

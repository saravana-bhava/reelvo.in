# utils/video_utils.py

"""
Handles video downloading, caching, trimming, and duration validation.
Supports Instagram Reels standards: portrait 1080x1920, duration 5–6s per clip.
"""

import os
import subprocess
import requests
import hashlib
from typing import Optional, Tuple
from dotenv import load_dotenv

load_dotenv()
DISABLE_CACHE = os.getenv("DISABLE_CACHE", "false").lower() == "true"

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
        print(f"[❌] ffprobe failed: {e}")
        return None


def trim_video(input_path: str, output_path: str, max_duration: int = 30) -> bool:
    """Trims a video to the specified max duration using FFmpeg."""
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
        print(f"[✂️] Trimmed video to {max_duration}s → {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[❌] FFmpeg trim error: {e}")
        return False


def download_video(
    url: str,
    output_path: str,
    min_duration: int = 5,
    max_duration: int = 6,
    return_url: bool = False
) -> Optional[str] | Tuple[Optional[str], Optional[str]]:
    """
    Downloads a video, optionally trims, and checks duration.

    Args:
        url: Source URL of video
        output_path: Local path to save video
        min_duration: Minimum allowed duration
        max_duration: Max allowed duration (trimmed if needed)
        return_url: If True, returns (output_path, url), else just output_path

    Returns:
        Output path or (output_path, url) if valid, else None or (None, None)
    """
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Hash + cache
        cache_dir = os.path.join("cache", "videos")
        os.makedirs(cache_dir, exist_ok=True)
        hashed = hashlib.md5(url.encode()).hexdigest()
        cached_path = os.path.join(cache_dir, f"{hashed}.mp4")

        # Use cached version if valid
        if not DISABLE_CACHE and os.path.exists(cached_path):
            print(f"[📦] Cached video found for URL: {url}")
            duration = get_video_duration(cached_path)
            if duration and duration >= min_duration:
                subprocess.run(["cp", cached_path, output_path], check=True)
                return (output_path, url) if return_url else output_path
            else:
                print("[⚠️] Cached video too short or unreadable. Deleting...")
                os.remove(cached_path)

        # Download fresh
        print(f"[⬇️] Downloading: {url}")
        temp_path = output_path + ".tmp"
        with requests.get(url, stream=True, timeout=15) as r:
            r.raise_for_status()
            with open(temp_path, "wb") as f:
                for chunk in r.iter_content(1024 * 1024):
                    f.write(chunk)

        duration = get_video_duration(temp_path)
        if duration is None:
            print("[⚠️] Duration unknown, saving as-is.")
            os.rename(temp_path, output_path)
            if not DISABLE_CACHE:
                subprocess.run(["cp", output_path, cached_path], check=True)
            return (output_path, url) if return_url else output_path

        if duration < min_duration:
            print(f"[⏹️] Skipping: too short ({duration:.2f}s < {min_duration}s)")
            os.remove(temp_path)
            return (None, None) if return_url else None

        if duration > max_duration:
            print(f"[⏱️] Trimming: {duration:.2f}s → {max_duration}s")
            success = trim_video(temp_path, output_path, max_duration)
            os.remove(temp_path)
            if success and not DISABLE_CACHE:
                subprocess.run(["cp", output_path, cached_path], check=True)
            return (output_path, url) if return_url else (output_path if success else None)

        # Save as-is
        os.rename(temp_path, output_path)
        print(f"[✅] Downloaded OK ({duration:.2f}s) → {output_path}")
        if not DISABLE_CACHE:
            subprocess.run(["cp", output_path, cached_path], check=True)

        return (output_path, url) if return_url else output_path

    except Exception as e:
        print(f"[❌] Video download error: {e}")
        return (None, None) if return_url else None

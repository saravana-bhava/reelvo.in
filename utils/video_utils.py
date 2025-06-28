# utils/video_utils.py

import os
import subprocess
import requests
import hashlib
from dotenv import load_dotenv

load_dotenv()

DISABLE_CACHE = os.getenv("DISABLE_CACHE", "false").lower() == "true"

def get_video_duration(filepath):
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
        print(f"[❌] Failed to get video duration: {e}")
        return None

def trim_video(input_path, output_path, max_duration=30):
    try:
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", input_path,
                "-t", str(max_duration),
                "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                "-c:a", "aac", "-b:a", "128k",
                output_path
            ],
            check=True
        )
        print(f"[✂️] Trimmed video to {max_duration}s → {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[❌] Failed to trim video: {e}")
        return False

def download_video(url, output_path, min_duration=5, max_duration=6, return_url=False):
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Setup cache
        cache_dir = os.path.join("cache", "videos")
        os.makedirs(cache_dir, exist_ok=True)
        hashed_name = hashlib.md5(url.encode()).hexdigest()
        cached_path = os.path.join(cache_dir, f"{hashed_name}.mp4")

        # Use cached version if available and allowed
        if not DISABLE_CACHE and os.path.exists(cached_path):
            print(f"[📦] Using cached video for URL: {url}")
            duration = get_video_duration(cached_path)
            if duration is not None and duration >= min_duration:
                subprocess.run(["cp", cached_path, output_path], check=True)
                return (output_path, url) if return_url else output_path
            else:
                print("[⚠️] Cached video invalid or too short. Re-downloading...")
                os.remove(cached_path)

        # Download new video
        print(f"[⬇️] Downloading video from: {url}")
        temp_path = output_path + ".tmp"
        with requests.get(url, stream=True, timeout=15) as r:
            r.raise_for_status()
            with open(temp_path, 'wb') as f:
                for chunk in r.iter_content(1024 * 1024):
                    f.write(chunk)

        duration = get_video_duration(temp_path)
        if duration is None:
            print("[⚠️] Skipping duration check, saving as-is.")
            os.rename(temp_path, output_path)
            if not DISABLE_CACHE:
                subprocess.run(["cp", output_path, cached_path], check=True)
            return (output_path, url) if return_url else output_path

        if duration < min_duration:
            print(f"[⏹️] Skipping video: too short ({duration:.2f}s < {min_duration}s)")
            os.remove(temp_path)
            return (None, None) if return_url else None

        if duration > max_duration:
            print(f"[⏱️] Video is {duration:.2f}s, trimming to {max_duration}s...")
            success = trim_video(temp_path, output_path, max_duration)
            os.remove(temp_path)
            if success and not DISABLE_CACHE:
                subprocess.run(["cp", output_path, cached_path], check=True)
            return (output_path if success else None, url) if return_url else (output_path if success else None)

        os.rename(temp_path, output_path)
        print(f"[✅] Video OK ({duration:.2f}s) → {output_path}")
        if not DISABLE_CACHE:
            subprocess.run(["cp", output_path, cached_path], check=True)
        return (output_path, url) if return_url else output_path

    except Exception as e:
        print(f"[❌] Failed to download video: {e}")
        return (None, None) if return_url else None

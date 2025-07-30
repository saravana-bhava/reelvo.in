# File: create_video.py

import logging
import os
import subprocess
import sys
import re
from dotenv import load_dotenv
from typing import List, Optional

# Ensure root directory is set
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(ROOT_DIR)
load_dotenv(os.path.join(ROOT_DIR, ".env"))

# Logger setup
logger = logging.getLogger("create_video")
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO)

# Import progress updater
try:
    from progress import update_progress
except ImportError:
    def update_progress(task_id, status, percent):  # dummy fallback
        pass

def create_video(
    video_path: str,
    inputs: List[str],
    audio_duration: float,
    filters: List[str],
    map_video: str,
    task_id: Optional[str] = None
) -> Optional[str]:
    """
    Final video render with FFmpeg using composed clips, overlays, and audio.

    Args:
        video_path (str): Output path to save final video.
        inputs (List[str]): Input ffmpeg arguments (e.g., ["-i", "clip1.mp4", "-i", "audio.mp3"]).
        audio_duration (float): Total duration of final video in seconds.
        filters (List[str]): FFmpeg filter_complex commands, joined with ';'.
        map_video (str): Output video stream reference (e.g., "[v]").
        task_id (Optional[str]): Task ID for progress tracking (if applicable).

    Returns:
        Optional[str]: Path to the created video, or None on failure.
    """

    logger.info("[🌐] Generating final Instagram Reel...")

    cmd = [
        "ffmpeg", *inputs,
        "-t", str(audio_duration),
        "-filter_complex", ";".join(filters),
        "-map", map_video, "-map", "1:a",
        "-c:v", "libx264", "-preset", "slow", "-crf", "18",
        "-b:v", "10M", "-minrate", "8M", "-maxrate", "12M", "-bufsize", "12M",
        "-c:a", "aac", "-ar", "44100", "-b:a", "256k", "-ac", "2",
        "-movflags", "+faststart", "-pix_fmt", "yuv420p", "-r", "30",
        "-y", video_path
    ]

    logger.info(f"[📦] FFmpeg command:\n{' '.join(cmd)}")

    try:
        process = subprocess.Popen(
            cmd,
            stderr=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        time_pattern = re.compile(r"time=(\d+):(\d+):(\d+\.\d+)")
        last_logged_percent = -1

        for line in process.stderr:
            line = line.strip()
            if "time=" in line:
                match = time_pattern.search(line)
                if match:
                    h, m, s = map(float, match.groups())
                    current_time = h * 3600 + m * 60 + s
                    percent = int((current_time / audio_duration) * 100)
                    percent = max(0, min(percent, 100))  # clamp to 0–100

                    if percent != last_logged_percent:
                        logger.info(f"[🎞️] Rendering progress: {percent}%")
                        if task_id:
                            update_progress(task_id, "🎞️ Rendering final video...", percent)
                        last_logged_percent = percent

        process.wait()

        if process.returncode == 0:
            logger.info(f"[✅] Reel created → {video_path}")
            if task_id:
                update_progress(task_id, "✅ Reel rendering complete.", 100)
            return video_path
        else:
            logger.error(f"[❌] FFmpeg exited with return code {process.returncode}")
            if task_id:
                update_progress(task_id, "❌ FFmpeg exited with error.", 100)
            return None

    except Exception as e:
        logger.exception(f"[❌] FFmpeg render failed: {e}")
        if task_id:
            update_progress(task_id, "❌ Render failed due to exception.", 100)
        return None


# CLI support for manual testing (optional)
if __name__ == "__main__":
    print("❌ This script is not meant to be run directly.")
    print("🔁 Use the `create_video()` function from within the main pipeline.")
    sys.exit(1)

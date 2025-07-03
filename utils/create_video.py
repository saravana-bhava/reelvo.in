# File: create_video.py

import logging
import os
import subprocess
import sys
from dotenv import load_dotenv
from typing import List, Optional

# Ensure root directory is set
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(ROOT_DIR)
load_dotenv(os.path.join(ROOT_DIR, ".env"))

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("create_video")


def create_video(
    video_path: str,
    inputs: List[str],
    audio_duration: float,
    filters: List[str],
    map_video: str
) -> Optional[str]:
    """
    Final video render with FFmpeg using composed clips, overlays, and audio.

    Args:
        video_path (str): Output path to save final video.
        inputs (List[str]): Input ffmpeg arguments, e.g., ["-i", "vid.mp4", "-i", "audio.mp3"]
        audio_duration (float): Duration of final video in seconds.
        filters (List[str]): FFmpeg filter_complex commands.
        map_video (str): Video stream map reference, e.g., "[v]"

    Returns:
        Optional[str]: Path to created video if success, else None.
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

    try:
        logger.info(f"[📦] FFmpeg command:\n{' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        logger.info(f"[✅] Reel created → {video_path}")
        return video_path
    except subprocess.CalledProcessError:
        logger.exception("[❌] FFmpeg render failed.")
        return None


# CLI support for manual test (optional)
if __name__ == "__main__":
    print("This script is not intended for direct CLI usage.")
    print("Use the `create_video()` function from within the main video generation pipeline.")

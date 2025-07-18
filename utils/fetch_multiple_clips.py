# File: utils/fetch_multiple_clips.py

import os
import re
import logging
import subprocess
import time
from typing import List
from dotenv import load_dotenv
from utils.pixabay_video import fetch_pixabay_video
from utils.pexels_video import fetch_pexels_video
from utils.progress_tracker import update_progress

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


def run_ffmpeg_with_progress(cmd: List[str], duration: float, task_id: str, base_msg: str, percent_start: int, percent_end: int):
    pattern = re.compile(r'time=(\d+):(\d+):(\d+\.\d+)')
    process = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True)

    last_percent = -1
    for line in process.stderr:
        if 'time=' in line:
            match = pattern.search(line)
            if match:
                h, m, s = map(float, match.groups())
                current = h * 3600 + m * 60 + s
                percent = int(current / duration * 100)
                smooth_percent = percent_start + int((percent / 100) * (percent_end - percent_start))
                if smooth_percent > last_percent:
                    update_progress(task_id, f"{base_msg} ({smooth_percent}%)", smooth_percent)
                    last_percent = smooth_percent

    process.wait()
    return process.returncode == 0


def download_video(src_path: str, dest_path: str, min_duration=5, max_duration=6, task_id=None, index=0, total=1) -> bool:
    """Trim a local video clip and apply basic formatting."""
    cmd = [
        "ffmpeg", "-y", "-i", src_path,
        "-ss", "0", "-t", str(max_duration),
        "-vf", "scale=1080:1920,fps=30",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "aac", "-ac", "2", "-b:a", "128k",
        "-movflags", "+faststart",
        dest_path
    ]
    try:
        if task_id:
            return run_ffmpeg_with_progress(cmd, max_duration, task_id, f"📥 Fallback clip {index+1}/{total}", 55, 65)
        subprocess.run(cmd, check=True)
        return True
    except Exception as e:
        logger.error(f"[❌] Failed to copy fallback clip '{src_path}' to '{dest_path}': {e}")
        return False


def fetch_multiple_clips(temp_dir: str, theme_name: str, language: str, script_text: str,
                         target_duration: float, task_id: str = None, start_percent: int = 55, end_percent: int = 65) -> List[str]:

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
            if download_video(fallback_local, clip_path, task_id=task_id, index=i, total=count):
                downloaded_clips.append(clip_path)
                found = True

        if not found:
            logger.warning(f"[⚠️] Clip {i+1} could not be downloaded from any source.")

        if task_id and found:
            percent = start_percent + int((i + 1) / count * (end_percent - start_percent))
            update_progress(task_id, f"📥 Downloaded clip {i + 1}/{count}", percent)

    return downloaded_clips


def concatenate_clips(temp_dir: str, theme_name: str, language: str, clips: List[str],
                      task_id: str = None, start_percent: int = 70, end_percent: int = 80) -> str:
    """Re-encode and concatenate video clips into a single vertical video with progress updates."""
    logger.info("[🔁] Re-encoding and concatenating clips...")

    reencoded_clips = []
    total_clips = len(clips)

    for i, clip in enumerate(clips):
        fixed = os.path.join(temp_dir, f"{theme_name}_{language}_fixed_clip{i+1}.mp4")
        cmd = [
            "ffmpeg", "-y", "-i", clip,
            "-vf", "scale=1080:1920,fps=30",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-c:a", "aac", "-ac", "2", "-b:a", "128k",
            "-movflags", "+faststart",
            fixed
        ]

        try:
            if task_id:
                success = run_ffmpeg_with_progress(cmd, CLIP_DURATION, task_id,
                                                   f"🔧 Re-encoding clip {i+1}/{total_clips}",
                                                   start_percent,
                                                   start_percent + int(((i+1)/total_clips)*(end_percent - start_percent) * 0.6)
                                                  )
            else:
                subprocess.run(cmd, check=True)
                success = True

            if success:
                reencoded_clips.append(fixed)

        except Exception as e:
            logger.error(f"[❌] Failed to re-encode {clip}: {e}")

    if not reencoded_clips:
        raise RuntimeError("[❌] No valid clips to concatenate.")

    list_file = os.path.join(temp_dir, "concat_list.txt")
    with open(list_file, "w") as f:
        for clip in reencoded_clips:
            f.write(f"file '{os.path.abspath(clip)}'\n")

    if task_id:
        update_progress(task_id, "📜 Creating concat list...", start_percent + int((end_percent - start_percent) * 0.7))

    combined_video_path = os.path.join(temp_dir, f"{theme_name}_{language}_combined.mp4")
    concat_cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file,
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        combined_video_path
    ]

    try:
        duration = CLIP_DURATION * len(reencoded_clips)
        if task_id:
            run_ffmpeg_with_progress(concat_cmd, duration, task_id, "📦 Merging clips", start_percent + 80, end_percent)
        else:
            subprocess.run(concat_cmd, check=True)

        if task_id:
            update_progress(task_id, "✅ All clips merged.", end_percent)

    except Exception as e:
        raise RuntimeError(f"[❌] Failed to concatenate clips: {e}")

    return combined_video_path

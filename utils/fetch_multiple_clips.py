# File: utils/fetch_multiple_clips.py

import os
import re
import logging
import subprocess
from typing import List, Set, Optional
from dotenv import load_dotenv
from utils.pixabay_video import fetch_pixabay_video
from utils.pexels_video import fetch_pexels_video
from utils.progress_tracker import get_stage_percent, update_progress

# Load environment variables
load_dotenv()

CLIP_DURATION = 5.5
FALLBACK_COUNT = 5

DISABLE_CACHE = os.getenv("DISABLE_CACHE", "false").lower() == "true"
USE_PEXELS = os.getenv("USE_PEXELS", "false").lower() == "true"
USE_PIXABAY = os.getenv("USE_PIXABAY", "true").lower() == "true"

logger = logging.getLogger("download_clips")
logging.basicConfig(level=logging.INFO)


def sanitize_english(text: str) -> str:
    """Extract ASCII/English-like words for better search accuracy."""
    words = re.findall(r'\b\w+\b', text.lower())
    ascii_words = [w for w in words if w.isascii()]
    return " ".join(ascii_words) or "inspiration"


def run_ffmpeg_with_progress(
    cmd: List[str],
    duration: float,
    task_id: str,
    base_msg: str,
    stage_index: int,
    substage_offset: float = 0.0,
    substage_scale: float = 1.0
) -> bool:
    """Run FFmpeg while monitoring stderr to update progress."""
    time_pattern = re.compile(r'time=(\d+):(\d+):(\d+\.\d+)')
    process = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True)

    last_percent = -1
    for line in process.stderr:
        if 'time=' in line:
            match = time_pattern.search(line)
            if match:
                h, m, s = map(float, match.groups())
                current = h * 3600 + m * 60 + s
                raw_progress = min(current / duration, 1.0)
                smooth_progress = substage_offset + raw_progress * substage_scale
                smooth_percent = get_stage_percent(stage_index, smooth_progress)
                if smooth_percent > last_percent:
                    update_progress(task_id, f"{base_msg} ({smooth_percent:.0f}%)", smooth_percent)
                    last_percent = smooth_percent

    process.wait()

    final_percent = get_stage_percent(stage_index, substage_offset + substage_scale)
    if last_percent < final_percent:
        update_progress(task_id, f"{base_msg} (100%)", final_percent)

    return process.returncode == 0


def download_video(
    src_path: str,
    dest_path: str,
    min_duration: int = 5,
    max_duration: int = 6,
    task_id: Optional[str] = None,
    index: int = 0,
    total: int = 1
) -> bool:
    """Trim and re-encode a local fallback video clip."""
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
            return run_ffmpeg_with_progress(
                cmd, max_duration, task_id,
                f"📥 Fallback clip {index+1}/{total}", 5
            )
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception as e:
        logger.error(f"[❌] Failed to trim fallback '{src_path}': {e}")
        return False


def fetch_multiple_clips(
    temp_dir: str,
    theme_name: str,
    language: str,
    script_text: str,
    target_duration: float,
    task_id: Optional[str] = None
) -> List[str]:
    """Fetch themed vertical clips using APIs or fallback if necessary."""
    logger.info("🎞️ Fetching video clips...")
    count = int(target_duration / CLIP_DURATION) + 1
    downloaded_clips = []
    used_video_ids: Set[int] = set()
    sources = []

    if USE_PEXELS:
        sources.append(fetch_pexels_video)
    if USE_PIXABAY:
        sources.append(fetch_pixabay_video)

    search_query = sanitize_english(script_text)
    os.makedirs(temp_dir, exist_ok=True)

    for i in range(count):
        clip_path = os.path.join(temp_dir, f"{theme_name}_{language}_clip{i+1}.mp4")
        found = False

        for source in sources:
            try:
                url = source(search_query, clip_path, used_video_ids=used_video_ids)
                if url:
                    downloaded_clips.append(clip_path)
                    found = True
                    break
            except Exception as e:
                logger.warning(f"[⚠️] {source.__name__} failed: {e}")

        if not found:
            fallback_index = (i % FALLBACK_COUNT) + 1
            fallback_file = os.path.join("assets", "clips", f"fallback{fallback_index}.mp4")
            if os.path.exists(fallback_file):
                success = download_video(fallback_file, clip_path, task_id=task_id, index=i, total=count)
                if success:
                    downloaded_clips.append(clip_path)
                    found = True
            else:
                logger.warning(f"[⚠️] Missing fallback: {fallback_file}")

        if not found:
            logger.warning(f"[❌] Could not fetch clip {i+1}/{count}")

        if task_id and found:
            progress = get_stage_percent(5, (i + 1) / count)
            update_progress(task_id, f"📥 Downloaded clip {i + 1}/{count}", progress)

    return downloaded_clips


def concatenate_clips(
    temp_dir: str,
    theme_name: str,
    language: str,
    clips: List[str],
    task_id: Optional[str] = None
) -> str:
    """Re-encode and concatenate vertical clips into a single file."""
    logger.info("[🔁] Re-encoding and concatenating clips...")

    reencoded_clips = []
    total = len(clips)

    for i, clip in enumerate(clips):
        fixed = os.path.join(temp_dir, f"{theme_name}_{language}_fixed_clip{i+1}.mp4")
        cmd = [
            "ffmpeg", "-y", "-ss", "0", "-t", str(CLIP_DURATION), "-i", clip,
            "-vf", "scale=1080:1920,fps=30",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-c:a", "aac", "-ac", "2", "-b:a", "128k",
            "-movflags", "+faststart",
            fixed
        ]
        try:
            if task_id:
                sub_offset = i / total
                sub_scale = 1.0 / total
                success = run_ffmpeg_with_progress(
                    cmd, CLIP_DURATION, task_id,
                    f"🔧 Re-encoding clip {i+1}/{total}",
                    stage_index=6,
                    substage_offset=sub_offset,
                    substage_scale=sub_scale
                )
            else:
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                success = True

            if success:
                reencoded_clips.append(fixed)
        except Exception:
            logger.exception(f"[❌] Failed to re-encode {clip}")

    if not reencoded_clips:
        raise RuntimeError("[❌] No clips to concatenate.")

    concat_list = os.path.join(temp_dir, "concat_list.txt")
    with open(concat_list, "w") as f:
        for clip in reencoded_clips:
            f.write(f"file '{os.path.abspath(clip)}'\n")

    combined_path = os.path.join(temp_dir, f"{theme_name}_{language}_combined.mp4")
    concat_cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list,
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        combined_path
    ]

    try:
        total_duration = CLIP_DURATION * total
        if task_id:
            run_ffmpeg_with_progress(concat_cmd, total_duration, task_id, "📦 Merging clips", stage_index=7)
            update_progress(task_id, "✅ All clips merged.", get_stage_percent(7, 1.0))
        else:
            subprocess.run(concat_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        raise RuntimeError(f"[❌] Concatenation failed: {e}")

    return combined_path

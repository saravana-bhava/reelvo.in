# File: progress_tracker.py

import time
from typing import Dict, Any

# In-memory task progress registry
progress_status: Dict[str, Dict[str, Any]] = {}

# Optional: Define progress weights centrally
PROGRESS_STAGES = [
    5,   # 0 - Setup
    5,   # 1 - Overlay
    10,  # 2 - Audio gen / processing
    10,  # 3 - Subtitles
    10,  # 4 - Translate + BGM
    15,  # 5 - Clip fetching
    15,  # 6 - Merging clips
    20,  # 7 - Final render
    10,  # 8 - Uploading
]


def start_progress(task_id: str) -> None:
    now = time.time()
    progress_status[task_id] = {
        "status": "🚀 Starting...",
        "percent": 0,
        "start_time": now,
        "elapsed": 0
    }


def update_progress(task_id: str, status: str, percent: int) -> None:
    if task_id not in progress_status:
        return

    now = time.time()
    task = progress_status[task_id]
    start = task.get("start_time", now)

    new_percent = min(max(int(percent), 0), 100)
    current_percent = task.get("percent", 0)
    current_status = task.get("status", "")

    if new_percent < current_percent:
        new_percent = current_percent

    if new_percent == current_percent and status == current_status:
        return

    task.update({
        "status": status,
        "percent": new_percent,
        "elapsed": int(now - start)
    })

    print(f"[Progress Status] Task {task_id} => {task}")


def finish_progress(task_id: str, status: str, percent: int = 100, download_url: str = None) -> None:
    if task_id not in progress_status:
        return

    now = time.time()
    start = progress_status[task_id].get("start_time", now)
    elapsed = now - start

    percent = min(max(int(percent), 0), 100)

    if download_url:
        progress_status[task_id]["download_url"] = download_url

    progress_status[task_id].update({
        "status": f"{status}<br>⏱️ Took {elapsed:.1f} sec",
        "percent": percent,
        "elapsed": int(elapsed)
    })


def get_progress(task_id: str) -> Dict[str, Any]:
    return progress_status.get(task_id, {
        "status": "❌ Task not found.",
        "percent": -1,
        "elapsed": 0
    })


def get_stage_percent(stage_index: int, sub_progress: float = 0.0) -> int:
    """
    Compute weighted progress percent based on stage and its subprogress.

    Args:
        stage_index (int): Current stage index (0-based).
        sub_progress (float): Progress within the stage (0.0 to 1.0).

    Returns:
        int: Total progress percent.
    """
    sub_progress = max(0.0, min(sub_progress, 1.0))
    base = sum(PROGRESS_STAGES[:stage_index])
    weight = PROGRESS_STAGES[stage_index] if stage_index < len(PROGRESS_STAGES) else 0
    return int(base + sub_progress * weight)

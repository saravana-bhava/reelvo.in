# File: utils/progress_tracker.py

"""
Handles tracking of task progress using SQLAlchemy ORM.
Each task has a task_id, status, percent, timestamps, and an optional download URL.
"""

import time
from typing import Dict, Any, Optional
from db import db
from db.models import ProgressTask

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
    task = ProgressTask.query.filter_by(task_id=task_id).first()

    if task:
        task.status = "🚀 Starting..."
        task.percent = 0
        task.start_time = now
        task.elapsed = 0
    else:
        task = ProgressTask(
            task_id=task_id,
            status="🚀 Starting...",
            percent=0,
            start_time=now,
            elapsed=0
        )
        db.session.add(task)

    db.session.commit()


def update_progress(task_id: str, status: str, percent: int) -> None:
    task = ProgressTask.query.filter_by(task_id=task_id).first()

    if not task:
        return

    now = time.time()
    elapsed = int(now - task.start_time)
    percent = min(max(percent, 0), 100)

    if percent < task.percent:
        percent = task.percent

    if percent == task.percent and status == task.status:
        return

    task.status = status
    task.percent = percent
    task.elapsed = elapsed
    db.session.commit()

    print(f"[Progress Status] Task {task_id} => {{'status': '{status}', 'percent': {percent}, 'elapsed': {elapsed}}}")


def finish_progress(task_id: str, status: str, percent: int = 100, download_url: Optional[str] = None) -> None:
    task = ProgressTask.query.filter_by(task_id=task_id).first()

    if not task:
        return

    now = time.time()
    elapsed = int(now - task.start_time)
    percent = min(max(percent, 0), 100)
    status_with_time = f"{status}<br>⏱️ Took {elapsed:.1f} sec"

    task.status = status_with_time
    task.percent = percent
    task.elapsed = elapsed
    task.download_url = download_url or ""
    db.session.commit()


def get_progress(task_id: str) -> Dict[str, Any]:
    task = ProgressTask.query.filter_by(task_id=task_id).first()

    if task:
        return {
            "status": task.status,
            "percent": task.percent,
            "elapsed": task.elapsed,
            "download_url": task.download_url or ""
        }

    return {
        "status": "❌ Task not found.",
        "percent": -1,
        "elapsed": 0
    }


def get_stage_percent(stage_index: int, sub_progress: float = 0.0) -> int:
    sub_progress = max(0.0, min(sub_progress, 1.0))
    base = sum(PROGRESS_STAGES[:stage_index])
    weight = PROGRESS_STAGES[stage_index] if stage_index < len(PROGRESS_STAGES) else 0
    return int(base + sub_progress * weight)


def progress_status(task_id: str) -> str:
    progress = get_progress(task_id)
    return f"{progress['status']} ({progress['percent']}%)"

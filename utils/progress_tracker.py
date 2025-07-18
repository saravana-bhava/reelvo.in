# File: progress.py

"""
In-memory task progress tracker for async operations.
Provides:
- start_progress(task_id)
- update_progress(task_id, status, percent)
- finish_progress(task_id, status, percent)
- get_progress(task_id)
"""

import time
from typing import Dict, Any

# In-memory task progress registry
progress_status: Dict[str, Dict[str, Any]] = {}


def start_progress(task_id: str) -> None:
    """
    Initialize a new task in the progress registry.

    Args:
        task_id (str): Unique identifier for the task.
    """
    now = time.time()
    progress_status[task_id] = {
        "status": "🚀 Starting...",
        "percent": 0,
        "start_time": now,
        "elapsed": 0
    }


def update_progress(task_id: str, status: str, percent: int) -> None:
    """
    Update the current progress of a task.
    Only logs changes to avoid spammy output.
    """
    if task_id not in progress_status:
        return  # Ignore update if task not initialized

    now = time.time()
    task = progress_status[task_id]
    start = task.get("start_time", now)

    # Clamp percent between 0–100
    new_percent = min(max(int(percent), 0), 100)
    current_percent = task.get("percent", 0)
    current_status = task.get("status", "")

    # Prevent regressions in percent
    if new_percent < current_percent:
        new_percent = current_percent

    # Avoid updating if nothing changed
    if new_percent == current_percent and status == current_status:
        return

    # Update and log
    task.update({
        "status": status,
        "percent": new_percent,
        "elapsed": int(now - start)
    })

    print(f"[Progress Status] Task {task_id} => {task}")

def finish_progress(task_id: str, status: str, percent: int = 100, download_url: str = None) -> None:
    """
    Mark a task as complete and finalize elapsed time.

    Args:
        task_id (str): Unique task identifier.
        status (str): Final status message.
        percent (int, optional): Final percent value. Defaults to 100.
    """
    if task_id not in progress_status:
        return  # Skip if task wasn't tracked

    now = time.time()
    start = progress_status[task_id].get("start_time", now)
    elapsed = now - start

    # Clamp percent between 0–100
    percent = min(max(int(percent), 0), 100)

    if download_url:
        progress_status[task_id]["download_url"] = download_url

    progress_status[task_id].update({
        "status": f"{status}<br>⏱️ Took {elapsed:.1f} sec",
        "percent": percent,
        "elapsed": int(elapsed)
    })

def get_progress(task_id: str) -> Dict[str, Any]:
    """
    Get the current progress status of a task.

    Args:
        task_id (str): Unique task identifier.

    Returns:
        dict: {
            "status": str,
            "percent": int,
            "elapsed": int
        }
    """
    return progress_status.get(task_id, {
        "status": "❌ Task not found.",
        "percent": -1,
        "elapsed": 0
    })

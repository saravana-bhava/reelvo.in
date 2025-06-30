# File: progress.py

"""
In-memory task progress tracker for async operations.
"""

import time
from typing import Dict, Any

# In-memory task status store
progress_status: Dict[str, Dict[str, Any]] = {}


def start_progress(task_id: str) -> None:
    """
    Initialize progress for a given task.

    Args:
        task_id (str): Unique identifier for the task.
    """
    progress_status[task_id] = {
        "status": "🚀 Starting...",
        "percent": 0,
        "start_time": time.time(),
        "elapsed": 0
    }


def update_progress(task_id: str, status: str, percent: int) -> None:
    """
    Update the status and percent of a running task.

    Args:
        task_id (str): Task identifier.
        status (str): Status message to show.
        percent (int): Progress percentage (0-100).
    """
    if task_id in progress_status:
        now = time.time()
        start = progress_status[task_id].get("start_time", now)
        progress_status[task_id].update({
            "status": status,
            "percent": percent,
            "elapsed": int(now - start)
        })


def finish_progress(task_id: str, status: str, percent: int = 100) -> None:
    """
    Mark the task as complete and update final elapsed time.

    Args:
        task_id (str): Task identifier.
        status (str): Final status message.
        percent (int, optional): Final percent. Defaults to 100.
    """
    if task_id in progress_status:
        now = time.time()
        start = progress_status[task_id].get("start_time", now)
        elapsed = now - start
        progress_status[task_id].update({
            "status": f"{status}<br>⏱️ Took {elapsed:.1f} sec",
            "percent": percent,
            "elapsed": int(elapsed)
        })


def get_progress(task_id: str) -> Dict[str, Any]:
    """
    Retrieve the current status of a task.

    Args:
        task_id (str): Task identifier.

    Returns:
        dict: Progress information including status, percent, and elapsed time.
    """
    return progress_status.get(task_id, {
        "status": "❌ Task not found.",
        "percent": -1,
        "elapsed": 0
    })

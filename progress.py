# progress.py

"""
In-memory task progress tracker for async operations.
"""

import time

# In-memory task status store
progress_status = {}


def start_progress(task_id):
    """
    Initialize progress for a given task.
    """
    progress_status[task_id] = {
        "status": "🚀 Starting...",
        "percent": 0,
        "start_time": time.time(),
        "elapsed": 0
    }


def update_progress(task_id, status, percent):
    """
    Update the status and percent of a running task.
    """
    if task_id in progress_status:
        now = time.time()
        start = progress_status[task_id].get("start_time", now)
        progress_status[task_id].update({
            "status": status,
            "percent": percent,
            "elapsed": int(now - start)
        })


def finish_progress(task_id, status, percent=100):
    """
    Mark the task as complete and update final elapsed time.
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


def get_progress(task_id):
    """
    Retrieve the current status of a task.
    """
    return progress_status.get(task_id, {
        "status": "❌ Task not found.",
        "percent": -1,
        "elapsed": 0
    })

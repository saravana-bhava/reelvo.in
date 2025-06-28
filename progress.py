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
        "start_time": time.time()
    }


def update_progress(task_id, status, percent):
    """
    Update the status and percent of a running task.
    """
    if task_id in progress_status:
        progress_status[task_id].update({
            "status": status,
            "percent": percent
        })


def finish_progress(task_id, status, percent=100):
    """
    Mark the task as complete and log the time taken.
    """
    if task_id in progress_status:
        elapsed = time.time() - progress_status[task_id]["start_time"]
        progress_status[task_id].update({
            "status": f"{status}<br>⏱️ Took {elapsed:.1f} sec",
            "percent": percent
        })


def get_progress(task_id):
    """
    Retrieve the current status of a task.
    """
    return progress_status.get(task_id, {
        "status": "❌ Task not found.",
        "percent": -1
    })

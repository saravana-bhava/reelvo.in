# progress.py

import time

# In-memory task status store
progress_status = {}

def start_progress(task_id):
    progress_status[task_id] = {
        "status": "🚀 Starting...",
        "percent": 0,
        "start_time": time.time()
    }

def update_progress(task_id, status, percent):
    if task_id in progress_status:
        progress_status[task_id].update({
            "status": status,
            "percent": percent
        })

def finish_progress(task_id, status, percent=100):
    if task_id in progress_status:
        elapsed = time.time() - progress_status[task_id]["start_time"]
        progress_status[task_id].update({
            "status": f"{status}<br>⏱️ Took {elapsed:.1f} sec",
            "percent": percent
        })

def get_progress(task_id):
    return progress_status.get(task_id, {
        "status": "❌ Task not found.",
        "percent": -1
    })

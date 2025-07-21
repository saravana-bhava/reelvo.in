# File: progress_tracker.py

import time
import sqlite3
from typing import Dict, Any, Optional

# SQLite setup
DB_PATH = "db/reelvo.db"

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


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS progress (
            task_id TEXT PRIMARY KEY,
            status TEXT,
            percent INTEGER,
            start_time REAL,
            elapsed INTEGER,
            download_url TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()


def start_progress(task_id: str) -> None:
    now = time.time()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO progress (task_id, status, percent, start_time, elapsed)
        VALUES (?, ?, ?, ?, ?)
    ''', (task_id, "🚀 Starting...", 0, now, 0))
    conn.commit()
    conn.close()


def update_progress(task_id: str, status: str, percent: int) -> None:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT start_time, percent, status FROM progress WHERE task_id = ?', (task_id,))
    row = c.fetchone()

    if not row:
        conn.close()
        return

    start_time, current_percent, current_status = row
    now = time.time()
    elapsed = int(now - start_time)
    new_percent = min(max(int(percent), 0), 100)

    if new_percent < current_percent:
        new_percent = current_percent

    if new_percent == current_percent and status == current_status:
        conn.close()
        return

    c.execute('''
        UPDATE progress
        SET status = ?, percent = ?, elapsed = ?
        WHERE task_id = ?
    ''', (status, new_percent, elapsed, task_id))
    conn.commit()
    conn.close()

    print(f"[Progress Status] Task {task_id} => {{'status': status, 'percent': {new_percent}, 'elapsed': {elapsed}}}")


def finish_progress(task_id: str, status: str, percent: int = 100, download_url: Optional[str] = None) -> None:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT start_time FROM progress WHERE task_id = ?', (task_id,))
    row = c.fetchone()

    if not row:
        conn.close()
        return

    start_time = row[0]
    now = time.time()
    elapsed = int(now - start_time)
    percent = min(max(int(percent), 0), 100)

    status_with_time = f"{status}<br>⏱️ Took {elapsed:.1f} sec"

    c.execute('''
        UPDATE progress
        SET status = ?, percent = ?, elapsed = ?, download_url = ?
        WHERE task_id = ?
    ''', (status_with_time, percent, elapsed, download_url, task_id))
    conn.commit()
    conn.close()


def get_progress(task_id: str) -> Dict[str, Any]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT status, percent, elapsed, download_url FROM progress WHERE task_id = ?', (task_id,))
    row = c.fetchone()
    conn.close()

    if row:
        status, percent, elapsed, download_url = row
        return {
            "status": status,
            "percent": percent,
            "elapsed": elapsed,
            "download_url": download_url or ""
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

# File: scripts/schedule_reels.py

"""
Assigns posting times for unscheduled reels (1 per day at 4PM).
Updates `scheduled_reels` table in SQLite (used by post_scheduled_reels.py).
Usage:
    python scripts/schedule_reels.py <user_email>
"""

import os
import sys
import logging
import sqlite3
from datetime import datetime, timedelta

# Constants
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(ROOT_DIR, "db", "reelvo.db")
DEFAULT_POST_HOUR = 16  # 4PM

# Logging setup
LOG_PATH = os.path.join(ROOT_DIR, "scheduler", "logs", "schedule_reels.log")
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_PATH), logging.StreamHandler()],
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("schedule_reels")


def connect_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_user_reel_history(conn, user_email):
    cursor = conn.execute(
        "SELECT video_path, script_path FROM reel_history WHERE email = ?", (user_email,)
    )
    return {os.path.basename(row["video_path"]): row["script_path"] for row in cursor.fetchall()}


def get_user_schedule(conn, user_email):
    cursor = conn.execute(
        "SELECT video, scheduled_at FROM scheduled_reels WHERE email = ?", (user_email,)
    )
    return [dict(row) for row in cursor.fetchall()]


def insert_schedule(conn, user_email, video, video_path, scheduled_for):
    conn.execute("""
        INSERT INTO scheduled_reels (email, video, scheduled_at, posted, created_at)
        VALUES (?, ?, ?, 0, CURRENT_TIMESTAMP)
    """, (user_email, video_path, scheduled_for))


def schedule_reels_for_user(user_email: str):
    with connect_db() as conn:
        history = get_user_reel_history(conn, user_email)
        user_schedule = get_user_schedule(conn, user_email)

        if not history:
            logger.warning(f"[{user_email}] ⚠️ No reel history found.")
            return

        scheduled_video_names = {os.path.basename(item["video"]) for item in user_schedule}

        # Determine starting post date
        start_date = datetime.now().replace(hour=DEFAULT_POST_HOUR, minute=0, second=0, microsecond=0)
        valid_dates = []

        for item in user_schedule:
            try:
                valid_dates.append(datetime.strptime(item["scheduled_at"], "%Y-%m-%d %H:%M:%S"))
            except Exception:
                logger.warning(f"[{user_email}] ⚠️ Skipping invalid date format: {item['scheduled_at']}")

        if valid_dates:
            latest = max(valid_dates)
            next_date = latest + timedelta(days=1)
            start_date = max(start_date, next_date)

        count = 0
        for video, script_path in history.items():
            if video in scheduled_video_names:
                continue

            video_path = f"output/{user_email}/videos/{video}"
            scheduled_for = start_date.strftime("%Y-%m-%d %H:%M:%S")

            insert_schedule(conn, user_email, video, video_path, scheduled_for)
            start_date += timedelta(days=1)
            count += 1

        conn.commit()

        if count:
            logger.info(f"[{user_email}] ✅ Scheduled {count} new reel(s).")
        else:
            logger.info(f"[{user_email}] ℹ️ No new reels to schedule.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/schedule_reels.py <user_email>")
        sys.exit(1)

    email = sys.argv[1].strip().lower()
    schedule_reels_for_user(email)

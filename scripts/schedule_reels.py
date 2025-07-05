# File: scripts/schedule_reels.py

"""
Assigns posting times for unscheduled reels (1 per day at 4PM).
Updates db/scheduled_posts.json (used by post_scheduled_reels.py).
"""

import os
import json
import sys
import logging
from datetime import datetime, timedelta

# Constants
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_DIR = os.path.join(ROOT_DIR, "db")
REEL_HISTORY_PATH = os.path.join(DB_DIR, "reel_history.json")
SCHEDULE_PATH = os.path.join(DB_DIR, "scheduled_posts.json")
DEFAULT_POST_HOUR = 16  # 4PM

# Logging
LOG_PATH = os.path.join(ROOT_DIR, "scheduler", "logs", "schedule_reels.log")
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_PATH), logging.StreamHandler()],
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("schedule_reels")


def load_json(path):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"❌ Failed to load JSON from {path}: {e}")
    return {}


def save_json(path, data):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"❌ Failed to save JSON to {path}: {e}")


def schedule_reels_for_user(user_email: str):
    history = load_json(REEL_HISTORY_PATH)
    scheduled = load_json(SCHEDULE_PATH)

    user_history = history.get(user_email, {})
    user_schedule = scheduled.get(user_email, [])

    if not isinstance(user_history, dict):
        logger.warning(f"[{user_email}] ⚠️ No valid reel history found.")
        return

    scheduled_video_names = {item.get("video") for item in user_schedule if isinstance(item, dict)}

    # Start from latest scheduled date or today
    all_dates = [item.get("scheduled_for") for item in user_schedule if "scheduled_for" in item]
    start_date = datetime.now().replace(hour=DEFAULT_POST_HOUR, minute=0, second=0, microsecond=0)
    if all_dates:
        try:
            latest = max(datetime.strptime(d, "%Y-%m-%d") for d in all_dates)
            start_date = max(start_date, latest + timedelta(days=1))
        except Exception:
            pass

    count = 0
    for video, script in user_history.items():
        if video in scheduled_video_names:
            continue

        video_path = f"output/{user_email}/videos/{video}"
        item = {
            "video": video,
            "video_path": video_path,
            "script": script,
            "scheduled_for": start_date.strftime("%Y-%m-%d"),
            "posted": False
        }
        user_schedule.append(item)
        start_date += timedelta(days=1)
        count += 1

    scheduled[user_email] = user_schedule
    save_json(SCHEDULE_PATH, scheduled)

    if count:
        logger.info(f"[{user_email}] ✅ Scheduled {count} new reel(s).")
    else:
        logger.info(f"[{user_email}] ℹ️ No new reels to schedule.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/schedule_reels.py <user_email>")
        sys.exit(1)

    email = sys.argv[1].strip().lower()
    schedule_reels_for_user(email)

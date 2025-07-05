# File: scheduler/schedule_reels.py

"""
Assigns posting times for unscheduled reels (1 per day, 4PM).
Writes to reels_metadata/<user>.json for compatibility with post_scheduled_reels.py.
"""

import os
import json
import sys
import logging
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "..", "db")
METADATA_DIR = os.path.join(BASE_DIR, "..", "reels_metadata")

# Paths
REEL_HISTORY_PATH = os.path.join(DB_DIR, "reel_history.json")
DEFAULT_POST_HOUR = 16  # 4 PM

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
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
    user_history = history.get(user_email, {})

    if not isinstance(user_history, dict):
        logger.warning(f"[{user_email}] ⚠️ No valid reel history found.")
        return

    metadata_path = os.path.join(METADATA_DIR, f"{user_email}.json")
    existing = []

    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception as e:
            logger.warning(f"[{user_email}] Failed to load existing schedule: {e}")
            existing = []

    existing_video_names = {os.path.basename(x.get("video_path", "")) for x in existing if isinstance(x, dict)}

    # Start scheduling from today 4PM or tomorrow 4PM
    now = datetime.now()
    post_date = now.replace(hour=DEFAULT_POST_HOUR, minute=0, second=0, microsecond=0)
    if now.hour >= DEFAULT_POST_HOUR:
        post_date += timedelta(days=1)

    scheduled = 0
    for video_name, script in user_history.items():
        if video_name in existing_video_names:
            continue

        video_path = f"output/{user_email}/videos/{video_name}"

        metadata = {
            "video_path": video_path,
            "caption": script,
            "scheduled_date": post_date.strftime("%Y-%m-%d"),
            "scheduled_time": f"{DEFAULT_POST_HOUR:02}:00",
            "status": "scheduled"
        }
        existing.append(metadata)
        post_date += timedelta(days=1)
        scheduled += 1

    save_json(metadata_path, existing)

    if scheduled:
        logger.info(f"[{user_email}] ✅ Scheduled {scheduled} new reel(s).")
    else:
        logger.info(f"[{user_email}] ℹ️ No new reels to schedule.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python schedule_reels.py <user_email>")
        sys.exit(1)

    user_email = sys.argv[1].strip().lower()
    schedule_reels_for_user(user_email)

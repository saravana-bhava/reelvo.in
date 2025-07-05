# File: scheduler/schedule_reels.py

"""
Assigns posting times for unscheduled reels (1 per day, 4PM).
Typically triggered after batch reel generation or manually via CLI.
Usage: python schedule_reels.py user@example.com
"""

import os
import json
import sys
import logging
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "..", "db")

# File paths
REEL_HISTORY_PATH = os.path.join(DB_DIR, "reel_history.json")
SCHEDULE_PATH = os.path.join(DB_DIR, "scheduled_posts.json")
DEFAULT_POST_HOUR = 16  # 4 PM

# Logging config
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("schedule_reels")


def load_json(path: str) -> dict:
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"❌ Failed to load JSON from {path}: {e}")
    return {}


def save_json(path: str, data: dict) -> None:
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except IOError as e:
        logger.error(f"❌ Failed to save JSON to {path}: {e}")


def schedule_reels_for_user(user_email: str) -> None:
    """Assign one post per day for unscheduled reels."""
    history = load_json(REEL_HISTORY_PATH)
    schedule = load_json(SCHEDULE_PATH)

    user_history = history.get(user_email, {})
    user_schedule = schedule.get(user_email)

    if not isinstance(user_history, dict):
        logger.warning(f"[{user_email}] ⚠️ No reel history found.")
        return

    if not isinstance(user_schedule, dict):
        user_schedule = {}

    already_scheduled = set(user_schedule.keys())

    # Start scheduling from 4PM today or tomorrow
    now = datetime.now()
    post_date = now.replace(hour=DEFAULT_POST_HOUR, minute=0, second=0, microsecond=0)
    if now.hour >= DEFAULT_POST_HOUR:
        post_date += timedelta(days=1)

    newly_scheduled = 0
    for filename, script in user_history.items():
        if filename in already_scheduled:
            continue

        user_schedule[filename] = {
            "script": script,
            "scheduled_for": post_date.strftime("%Y-%m-%d"),
            "posted": False
        }
        post_date += timedelta(days=1)
        newly_scheduled += 1

    if newly_scheduled:
        schedule[user_email] = user_schedule
        save_json(SCHEDULE_PATH, schedule)
        logger.info(f"[{user_email}] ✅ Scheduled {newly_scheduled} new reel(s).")
    else:
        logger.info(f"[{user_email}] ℹ️ No new reels to schedule.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python schedule_reels.py <user_email>")
        sys.exit(1)

    email_arg = sys.argv[1].strip().lower()
    schedule_reels_for_user(email_arg)

# File: scheduler/schedule_reels.py

"""
Assigns scheduled posting times for each reel generated per user.
Should be run after batch reel generation to queue reels chronologically.
"""

import os
import json
import sys
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "..", "db")

# Constants
REEL_HISTORY_PATH = os.path.join(DB_DIR, "reel_history.json")
SCHEDULE_PATH = os.path.join(DB_DIR, "scheduled_posts.json")
DEFAULT_POST_HOUR = 16  # 4 PM


def load_json(path: str) -> dict:
    """Load JSON data from file, or return empty dict if file doesn't exist."""
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_json(path: str, data: dict) -> None:
    """Save dictionary data to a JSON file with UTF-8 encoding."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"❌ Failed to save schedule file: {e}")


def schedule_reels_for_user(user_name: str) -> None:
    """
    Schedule all unscheduled reels for a given user, one per day.
    """
    history = load_json(REEL_HISTORY_PATH)
    schedule = load_json(SCHEDULE_PATH)

    user_history = history.get(user_name, {})
    user_schedule = schedule.get(user_name, {})

    if not isinstance(user_schedule, dict):
        user_schedule = {}

    already_scheduled = set(user_schedule.keys())

    # Start scheduling from today 4 PM (or tomorrow if already past 4 PM)
    now = datetime.now()
    post_date = now.replace(hour=DEFAULT_POST_HOUR, minute=0, second=0, microsecond=0)
    if now.hour >= DEFAULT_POST_HOUR:
        post_date += timedelta(days=1)

    newly_scheduled = 0
    for filename, script in user_history.items():
        if filename in already_scheduled:
            continue  # Skip already scheduled reels

        user_schedule[filename] = {
            "script": script,
            "scheduled_for": post_date.isoformat(),
            "posted": False
        }
        post_date += timedelta(days=1)
        newly_scheduled += 1

    schedule[user_name] = user_schedule
    save_json(SCHEDULE_PATH, schedule)

    print(f"✅ Scheduled {newly_scheduled} new reel(s) for user: {user_name}")


if __name__ == "__main__":
    user_arg = sys.argv[1] if len(sys.argv) > 1 else "demo_user"
    schedule_reels_for_user(user_arg)

# File: scheduler/schedule_reels.py
"""
Assigns scheduled posting times for each reel generated per user.
This should be run right after batch reel generation.
"""

import os
import json
from datetime import datetime, timedelta

REEL_HISTORY_PATH = "reel_history.json"
SCHEDULE_PATH = "scheduled_posts.json"

DEFAULT_POST_HOUR = 16  # 4 PM


def load_json(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def schedule_reels_for_user(username):
    history = load_json(REEL_HISTORY_PATH)
    schedule = load_json(SCHEDULE_PATH)

    user_history = history.get(username, {})
    user_schedule = schedule.get(username, {})

    # Get all existing scheduled filenames
    existing = set(user_schedule.keys())
    start_date = datetime.now().replace(hour=DEFAULT_POST_HOUR, minute=0, second=0, microsecond=0)
    if datetime.now().hour >= DEFAULT_POST_HOUR:
        start_date += timedelta(days=1)

    post_date = start_date

    for filename, data in user_history.items():
        if filename in existing:
            continue  # Already scheduled

        user_schedule[filename] = {
            "script": data["script"],
            "scheduled_for": post_date.isoformat(),
            "posted": False
        }
        post_date += timedelta(days=1)

    schedule[username] = user_schedule
    save_json(SCHEDULE_PATH, schedule)
    print(f"✅ Scheduled {len(user_schedule)} reels for user: {username}")


if __name__ == "__main__":
    import sys
    user = sys.argv[1] if len(sys.argv) > 1 else "demo_user"
    schedule_reels_for_user(user)

# File: scheduler/post_scheduled.py

"""
Posts scheduled reels for today to Instagram.
Should be triggered daily (e.g., via CRON at 4 PM).
"""

import os
import json
import logging
from datetime import datetime
from utils.instagram_posting import post_to_instagram
from utils.user_db import get_user_token_data

# Paths
SCHEDULE_FILE = "scheduled_posts.json"
HISTORY_FILE = "reel_history.json"

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("post_scheduled")

def load_json(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def post_due_reels():
    logger.info("📤 Starting scheduled reel poster...")

    schedule = load_json(SCHEDULE_FILE)
    history = load_json(HISTORY_FILE)
    today_str = datetime.now().strftime("%Y-%m-%d")

    for username, user_schedules in schedule.items():
        token_data = get_user_token_data(username)
        if not token_data or "access_token" not in token_data:
            logger.warning(f"[{username}] ❌ No valid Instagram token found.")
            continue

        for item in user_schedules:
            if item.get("posted"):
                continue  # Already posted

            if item.get("scheduled_for") <= today_str:
                video = item["video"]
                caption = history.get(username, {}).get(video, "")
                video_path = os.path.join("output", username, video)

                logger.info(f"[{username}] ⏰ Posting scheduled reel: {video}...")
                try:
                    success = post_to_instagram(username, video_path, caption)
                    if success:
                        item["posted"] = True
                        logger.info(f"[✅] Posted: {video}")
                    else:
                        logger.warning(f"[⚠️] Failed to post: {video}")
                except Exception as e:
                    logger.exception(f"[❌] Error posting {video}: {e}")

    save_json(SCHEDULE_FILE, schedule)
    logger.info("✅ Finished scheduled posting process.")

if __name__ == "__main__":
    post_due_reels()

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

# File paths
SCHEDULE_FILE = "scheduled_posts.json"
HISTORY_FILE = "reel_history.json"
OUTPUT_DIR = "output"

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("post_scheduled")


def load_json(path):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"❌ Failed to load JSON from {path}: {e}")
            return {}
    return {}


def save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"❌ Failed to save JSON to {path}: {e}")


def post_due_reels():
    logger.info("📤 Starting scheduled reel poster...")

    schedule = load_json(SCHEDULE_FILE)
    history = load_json(HISTORY_FILE)
    today_str = datetime.now().strftime("%Y-%m-%d")

    for username, user_schedule in schedule.items():
        token_data = get_user_token_data(username)
        if not token_data or "access_token" not in token_data:
            logger.warning(f"[{username}] ⚠️ No valid Instagram token found.")
            continue

        for video, metadata in user_schedule.items():
            if metadata.get("posted"):
                continue

            scheduled_date = metadata.get("scheduled_for")
            if scheduled_date and scheduled_date <= today_str:
                caption = metadata.get("script") or history.get(username, {}).get(video, "")
                video_path = os.path.join(OUTPUT_DIR, username, video)

                if not os.path.exists(video_path):
                    logger.warning(f"[{username}] ❌ Video not found: {video_path}")
                    continue

                logger.info(f"[{username}] ⏰ Posting scheduled reel: {video}")
                try:
                    success = post_to_instagram(username, video_path, caption)
                    if success:
                        metadata["posted"] = True
                        metadata["posted_at"] = datetime.now().isoformat()
                        logger.info(f"[{username}] ✅ Posted: {video}")
                    else:
                        logger.warning(f"[{username}] ⚠️ Failed to post: {video}")
                except Exception as e:
                    logger.exception(f"[{username}] ❌ Exception posting {video}: {e}")

    save_json(SCHEDULE_FILE, schedule)
    logger.info("✅ Finished scheduled posting process.")


if __name__ == "__main__":
    post_due_reels()

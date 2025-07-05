# File: scheduler/post_scheduled.py

"""
Posts scheduled reels for today to Instagram.
Should be triggered daily, e.g.:
0 16 * * * /usr/bin/python3 /path/to/post_scheduled.py
"""

import os
import json
import logging
from datetime import datetime
from utils.instagram_posting import post_to_instagram
from utils.user_db import get_user_token_data

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "..", "db")

# File paths
HISTORY_FILE = os.path.join(DB_DIR, "reel_history.json")
SCHEDULE_FILE = os.path.join(DB_DIR, "scheduled_posts.json")
OUTPUT_DIR = "output"

# Logging config
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
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"❌ Failed to load JSON from {path}: {e}")
            return {}
    return {}


def save_json(path, data):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"❌ Failed to save JSON to {path}: {e}")


def post_due_reels():
    logger.info("📤 Starting scheduled reel poster...")

    schedule = load_json(SCHEDULE_FILE)
    history = load_json(HISTORY_FILE)
    today = datetime.now().strftime("%Y-%m-%d")

    for user_email, user_schedule in schedule.items():
        token_data = get_user_token_data(user_email)
        if not token_data or "access_token" not in token_data:
            logger.warning(f"[{user_email}] ⚠️ No valid Instagram token.")
            continue

        if not isinstance(user_schedule, list):
            logger.warning(f"[{user_email}] ⚠️ Malformed schedule. Skipping.")
            continue

        for metadata in user_schedule:
            if not isinstance(metadata, dict):
                continue

            if metadata.get("posted"):
                continue

            scheduled_date = metadata.get("scheduled_for")
            video = metadata.get("video")

            if not video or not scheduled_date or scheduled_date > today:
                continue

            video_path = os.path.join(OUTPUT_DIR, user_email, "videos", video)
            if not os.path.exists(video_path):
                logger.warning(f"[{user_email}] ❌ Video not found: {video_path}")
                continue

            # Caption fallback
            caption = metadata.get("script") or history.get(user_email, {}).get(video, "")

            logger.info(f"[{user_email}] ⏰ Posting: {video}")
            try:
                success = post_to_instagram(user_email, video_path, caption)
                if success:
                    metadata["posted"] = True
                    metadata["posted_at"] = datetime.now().isoformat()
                    logger.info(f"[{user_email}] ✅ Posted: {video}")
                else:
                    logger.warning(f"[{user_email}] ⚠️ Failed to post: {video}")
            except Exception as e:
                logger.exception(f"[{user_email}] ❌ Exception posting {video}: {e}")

    save_json(SCHEDULE_FILE, schedule)
    logger.info("✅ Finished scheduled posting.")


if __name__ == "__main__":
    post_due_reels()

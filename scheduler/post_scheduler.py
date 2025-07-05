# File: scheduler/post_scheduled_reels.py

"""
Posts reels scheduled for today at a specific hour via Graph API.
Typically triggered via CRON (e.g. daily at 16:00).
"""

import os
import json
import logging
from datetime import datetime
from utils.instagram_upload import post_reel
from utils.user_db import get_user_token

SCHEDULE_DIR = "reels_metadata"
SCHEDULED_HOUR = "16:00"

# Logger setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("scheduled_reels")


def run_scheduler():
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")

    logger.info("📅 Checking scheduled reels...")

    if not os.path.exists(SCHEDULE_DIR):
        logger.warning(f"⚠️ Schedule directory '{SCHEDULE_DIR}' does not exist.")
        return

    for user_file in os.listdir(SCHEDULE_DIR):
        if not user_file.endswith(".json"):
            continue

        user_email = user_file.replace(".json", "")
        user_path = os.path.join(SCHEDULE_DIR, user_file)

        try:
            with open(user_path, "r", encoding="utf-8") as f:
                reels = json.load(f)
        except Exception as e:
            logger.error(f"[{user_email}] ❌ Failed to load schedule: {e}")
            continue

        if not isinstance(reels, list):
            logger.warning(f"[{user_email}] ⚠️ Invalid format. Expected list.")
            continue

        updated = False

        for reel in reels:
            if not isinstance(reel, dict):
                continue

            status = reel.get("status")
            scheduled_date = reel.get("scheduled_date")
            scheduled_time = reel.get("scheduled_time")
            video_path = reel.get("video_path")

            if (
                status == "scheduled"
                and scheduled_date == today
                and scheduled_time == SCHEDULED_HOUR
            ):
                if not video_path or not os.path.exists(video_path):
                    logger.warning(f"[{user_email}] 🚫 Video not found: {video_path}")
                    continue

                token_info = get_user_token(user_email)
                if not token_info:
                    logger.warning(f"[{user_email}] ⚠️ Missing Instagram token.")
                    continue

                try:
                    post_reel(
                        token_info=token_info,
                        video_path=video_path,
                        caption=reel.get("caption", "")
                    )
                    reel["status"] = "posted"
                    reel["posted_at"] = now.isoformat()
                    updated = True
                    logger.info(f"[{user_email}] ✅ Posted reel: {video_path}")
                except Exception as e:
                    logger.exception(f"[{user_email}] ❌ Failed to post: {video_path}")
                    reel["status"] = "failed"  # Optional
                    updated = True

        if updated:
            try:
                with open(user_path, "w", encoding="utf-8") as f:
                    json.dump(reels, f, indent=2, ensure_ascii=False)
                logger.info(f"[{user_email}] 💾 Schedule updated.")
            except Exception as e:
                logger.error(f"[{user_email}] ❌ Failed to write updated schedule: {e}")

    logger.info("✅ Finished scheduled reel processing.")


if __name__ == "__main__":
    run_scheduler()

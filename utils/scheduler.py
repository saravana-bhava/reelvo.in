# File: utils/scheduler.py

"""
Background scheduler that checks for scheduled reels and auto-posts to Instagram.
Runs in a loop, posting when the scheduled time is met.

Data source: db/scheduled_posts.json
"""

import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any
from utils.instagram import post_to_instagram

# Constants
SCHEDULED_PATH = "db/scheduled_posts.json"
logger = logging.getLogger("reelvo")
logging.basicConfig(level=logging.INFO)


def scheduler_runner() -> None:
    """
    Continuously checks and posts reels scheduled for Instagram.
    This function is meant to be run as a background thread or process.
    """
    logger.info("⏱️ Starting background scheduler...")
    os.makedirs(os.path.dirname(SCHEDULED_PATH), exist_ok=True)

    while True:
        if not os.path.exists(SCHEDULED_PATH):
            time.sleep(60)
            continue

        try:
            with open(SCHEDULED_PATH, "r", encoding="utf-8") as f:
                all_jobs: Dict[str, Dict[str, Any]] = json.load(f)

            for user_email, jobs in all_jobs.items():
                if not isinstance(jobs, dict):
                    continue  # Defensive: skip malformed job list

                for video_name, job in jobs.items():
                    try:
                        if job.get("posted"):
                            continue  # Already posted

                        scheduled_for = job.get("scheduled_for")
                        if not scheduled_for:
                            continue  # Missing scheduled time

                        # Check if scheduled time has arrived
                        scheduled_time = datetime.fromisoformat(scheduled_for)
                        now = datetime.now()
                        if now >= scheduled_time:
                            logger.info(f"📤 Posting scheduled reel for {user_email} → {video_name}")

                            video_path = job.get("video_path") or f"output/final/{video_name}"
                            caption = job.get("caption", "Scheduled post")

                            post_result = post_to_instagram(
                                video_path=video_path,
                                caption=caption,
                                user_name=user_email
                            )

                            # Update job status
                            job["posted"] = True
                            job["result"] = post_result
                            logger.info(f"[✅] Posted successfully → {video_name}")

                    except Exception as e:
                        job["error"] = str(e)
                        logger.error(f"[❌] Error posting {video_name} for {user_email}: {e}")

            # Write updated job states back to file
            with open(SCHEDULED_PATH, "w", encoding="utf-8") as f:
                json.dump(all_jobs, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.warning(f"[⚠️] Failed to process scheduled jobs: {e}")

        time.sleep(60)  # Wait 1 minute before checking again

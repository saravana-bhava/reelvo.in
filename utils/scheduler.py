# File: utils/scheduler.py

import os
import json
import time
import logging
from datetime import datetime
from utils.instagram import post_to_instagram

SCHEDULED_PATH = "db/scheduled_posts.json"
logger = logging.getLogger("reelvo")


def scheduler_runner():
    """Continuously checks for scheduled jobs and posts them if time is met."""
    logger.info("⏱️ Starting background scheduler...")
    os.makedirs(os.path.dirname(SCHEDULED_PATH), exist_ok=True)

    while True:
        if not os.path.exists(SCHEDULED_PATH):
            time.sleep(60)
            continue

        try:
            with open(SCHEDULED_PATH, "r") as f:
                all_jobs = json.load(f)

            for user_email, jobs in all_jobs.items():
                if not isinstance(jobs, dict):
                    continue

                for video_name, job in jobs.items():
                    try:
                        if job.get("posted"):
                            continue

                        scheduled_for = job.get("scheduled_for")
                        if not scheduled_for:
                            continue

                        # Check if scheduled time is due
                        scheduled_time = datetime.fromisoformat(scheduled_for)
                        if datetime.now() >= scheduled_time:
                            logger.info(f"📤 Posting scheduled reel for {user_email}...")

                            post_result = post_to_instagram(
                                video_path=job.get("video_path", f"output/final/{video_name}"),
                                caption=job.get("caption", "Scheduled post"),
                                user_name=user_email
                            )

                            job["posted"] = True
                            job["result"] = post_result
                            logger.info(f"[✅] Successfully posted: {video_name}")

                    except Exception as e:
                        job["error"] = str(e)
                        logger.error(f"[❌] Failed to post {video_name} for {user_email}: {e}")

            with open(SCHEDULED_PATH, "w") as f:
                json.dump(all_jobs, f, indent=2)

        except Exception as e:
            logger.warning(f"[⚠️] Failed to process scheduled jobs: {e}")

        time.sleep(60)

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

            updated_all_jobs = {}

            for user_name, jobs in all_jobs.items():
                updated_jobs = []
                for job in jobs:
                    try:
                        if (
                            job.get("status") == "pending"
                            and datetime.now().isoformat() >= job.get("scheduled_time", "")
                        ):
                            logger.info(f"📤 Posting scheduled reel for {user_name}...")

                            post_result = post_to_instagram(
                                video_path=job["video_path"],
                                caption=job.get("caption", "Scheduled post"),
                                user_name=user_name
                            )

                            job["status"] = "posted"
                            job["result"] = post_result
                            logger.info(f"[✅] Successfully posted: {job['video_path']}")
                        else:
                            updated_jobs.append(job)
                            continue

                    except Exception as e:
                        job["status"] = "error"
                        job["error"] = str(e)
                        logger.error(f"[❌] Failed to post: {e}")

                    updated_jobs.append(job)

                updated_all_jobs[user_name] = updated_jobs

            with open(SCHEDULED_PATH, "w") as f:
                json.dump(updated_all_jobs, f, indent=2)

        except Exception as e:
            logger.warning(f"[⚠️] Failed to process scheduled jobs: {e}")

        time.sleep(60)

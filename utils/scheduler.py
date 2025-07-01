# File: scheduler_runner.py

import os
import json
import time
import logging
from datetime import datetime
from utils.instagram import post_to_instagram

SCHEDULED_JOBS_DIR = "scheduled_jobs"
logger = logging.getLogger("reelvo")

def scheduler_runner():
    """Continuously checks for scheduled jobs and posts them if time is met."""
    logger.info("⏱️ Starting background scheduler...")
    os.makedirs(SCHEDULED_JOBS_DIR, exist_ok=True)

    while True:
        for fname in os.listdir(SCHEDULED_JOBS_DIR):
            fpath = os.path.join(SCHEDULED_JOBS_DIR, fname)
            try:
                with open(fpath, "r") as f:
                    jobs = json.load(f)

                updated_jobs = []
                for job in jobs:
                    try:
                        if job["status"] == "pending" and datetime.now().isoformat() >= job["scheduled_time"]:
                            logger.info(f"📤 Posting scheduled reel for {job['username']}...")

                            post_result = post_to_instagram(
                                video_path=job["video_path"],
                                caption=job.get("caption", "Scheduled post"),
                                username=job["username"]
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

                with open(fpath, "w") as f:
                    json.dump(updated_jobs, f, indent=2)

            except Exception as e:
                logger.warning(f"[⚠️] Failed to process scheduled jobs file {fname}: {e}")

        time.sleep(60)

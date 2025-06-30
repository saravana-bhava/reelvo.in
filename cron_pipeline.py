# File: cron_pipeline.py

"""
Scheduled pipeline for generating reels for all categories.
Typically triggered via CRON or external task scheduler.
"""

import time
import logging
import os
import sys
from run_pipeline import run_pipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("cron_pipeline")

# Constants
CATEGORIES = ["motivation", "success", "life", "inspiration", "sad"]
DEFAULT_USERNAME = os.getenv("DEFAULT_USERNAME", "demo")
SLEEP_BETWEEN = int(os.getenv("SLEEP_BETWEEN_RUNS", "5"))  # seconds


def run_all_categories_for_user(username: str):
    """
    Run reel generation for all predefined categories for a given user.

    Args:
        username (str): Username for whom to generate reels.
    """
    logger.info(f"🌀 Starting CRON reel generation for user: {username}")

    for category in CATEGORIES:
        try:
            logger.info(f"🕒 Generating reel for category: {category}")
            output_path = run_pipeline(category, username)

            if output_path:
                logger.info(f"[✅] Completed: {output_path}")
            else:
                logger.warning(f"[⚠️] Generation failed for category: {category}")

            time.sleep(SLEEP_BETWEEN)

        except Exception as e:
            logger.exception(f"[❌] Error generating category '{category}': {e}")

    logger.info("✅ All CRON-based reel generations completed.\n")


if __name__ == "__main__":
    try:
        user = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_USERNAME
        run_all_categories_for_user(user)
    except Exception as main_err:
        logger.exception(f"❌ Fatal error in CRON pipeline: {main_err}")

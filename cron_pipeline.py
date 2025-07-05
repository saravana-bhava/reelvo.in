# File: cron_pipeline.py

"""
Scheduled pipeline for generating reels for all categories.
Typically triggered via CRON or external task scheduler.
"""

import time
import logging
import os
import sys
from dotenv import load_dotenv
from run_pipeline import run_pipeline

# ----------------- Load Environment -----------------
load_dotenv()

# ----------------- Logging Configuration -----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("cron_pipeline")

# ----------------- Constants -----------------
CATEGORIES = ["motivation", "success", "life", "inspiration", "sad"]
DEFAULT_EMAIL = os.getenv("DEFAULT_EMAIL", "developer@sazm.in")
SLEEP_BETWEEN = int(os.getenv("SLEEP_BETWEEN_RUNS", "5"))


def run_all_categories_for_user(user_name: str):
    """
    Run reel generation for all predefined categories for a given user.

    Args:
        user_name (str): Username for whom to generate reels.
    """
    user_name = user_name.strip()
    logger.info(f"🌀 Starting CRON reel generation for user: {user_name}")

    for i, category in enumerate(CATEGORIES, start=1):
        try:
            logger.info(f"[{i}/{len(CATEGORIES)}] 🕒 Generating reel for category: {category}")
            output_path = run_pipeline(category, user_name)

            if output_path:
                logger.info(f"[✅] Reel created → {output_path}")
            else:
                logger.warning(f"[⚠️] Failed to generate reel for: {category}")

        except Exception as e:
            logger.exception(f"[❌] Error generating reel for category '{category}': {e}")

        if i < len(CATEGORIES):
            time.sleep(SLEEP_BETWEEN)

    logger.info(f"🏁 All scheduled reels generated for user: {user_name}")


if __name__ == "__main__":
    try:
        user = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_EMAIL
        run_all_categories_for_user(user)
    except Exception as main_err:
        logger.exception(f"[💥] Fatal error in CRON pipeline: {main_err}")
        sys.exit(1)

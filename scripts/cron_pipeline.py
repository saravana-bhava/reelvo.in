# File: scripts/run_category_pipeline.py

"""
Scheduled pipeline for generating reels for all categories.
Typically triggered via CRON or external scheduler.
"""

import os
import sys
import time
import logging
from dotenv import load_dotenv
from scripts.run_generation_pipeline import run_pipeline

# ----------------- Load Environment -----------------
load_dotenv()

# ----------------- Logging -----------------
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOG_PATH = os.path.join(ROOT_DIR, "scheduler", "logs", "category_pipeline.log")
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler()
    ],
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("category_pipeline")

# ----------------- Constants -----------------
CATEGORIES = ["motivation", "success", "life", "inspiration", "sad"]
DEFAULT_EMAIL = os.getenv("DEFAULT_EMAIL", "developer@sazm.in")
SLEEP_BETWEEN = int(os.getenv("SLEEP_BETWEEN_RUNS", "5"))


def run_all_categories_for_user(user_email: str):
    """
    Run reel generation for all predefined categories for a given user.

    Args:
        user_email (str): Email of the user.
    """
    user_email = user_email.strip()
    logger.info(f"🌀 Starting category-based reel generation for user: {user_email}")

    for i, category in enumerate(CATEGORIES, start=1):
        try:
            logger.info(f"[{i}/{len(CATEGORIES)}] Generating reel for: {category}")
            output_path = run_pipeline(category, user_email)

            if output_path:
                logger.info(f"[✅] Reel created → {output_path}")
            else:
                logger.warning(f"[⚠️] Generation failed for: {category}")

        except Exception as e:
            logger.exception(f"[❌] Error generating reel for category '{category}': {e}")

        if i < len(CATEGORIES):
            time.sleep(SLEEP_BETWEEN)

    logger.info(f"🏁 All reels generated for user: {user_email}")


if __name__ == "__main__":
    try:
        user = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_EMAIL
        run_all_categories_for_user(user)
    except Exception as main_err:
        logger.exception(f"[💥] Fatal error in category pipeline: {main_err}")
        sys.exit(1)

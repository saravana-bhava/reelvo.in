# File: scripts/run_category_pipeline.py

"""
Scheduled pipeline for generating reels for all categories.
Typically triggered via CRON or external scheduler.

Usage:
    python scripts/run_category_pipeline.py [user_email]

Environment Variables:
    DEFAULT_EMAIL           → fallback user email if not provided
    SLEEP_BETWEEN_RUNS      → delay (in seconds) between each reel (default: 5)
"""

import os
import sys
import time
import logging
from dotenv import load_dotenv
from scripts.run_generation_pipeline import run_pipeline

# ----------------- Load Environment -----------------
load_dotenv()

# ----------------- Logging Setup -----------------
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOG_PATH = os.path.join(ROOT_DIR, "scheduler", "logs", "category_pipeline.log")
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="📋 %(asctime)s [%(levelname)s] %(message)s",
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
    Generate reels for all categories for the specified user.

    Args:
        user_email (str): User's email address or slug.
    """
    user_email = user_email.strip().lower()
    logger.info(f"🚀 Starting scheduled generation for user: {user_email}")

    for i, category in enumerate(CATEGORIES, start=1):
        try:
            logger.info(f"[{i}/{len(CATEGORIES)}] 🎬 Generating: {category}")
            result = run_pipeline(category, user_email)

            if result:
                logger.info(f"✅ Created: {result}")
            else:
                logger.warning(f"⚠️ Failed: {category}")
        except Exception as e:
            logger.exception(f"❌ Exception during '{category}' generation: {e}")

        if i < len(CATEGORIES):
            time.sleep(SLEEP_BETWEEN)

    logger.info(f"🏁 Finished all categories for user: {user_email}")

if __name__ == "__main__":
    try:
        user = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_EMAIL
        run_all_categories_for_user(user)
    except Exception as e:
        logger.exception(f"💥 Fatal error in category pipeline: {e}")
        sys.exit(1)

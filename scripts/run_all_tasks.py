# File: scripts/run_all_tasks.py

"""
Batch runner to generate reels for all categories for a given user.
Typically used for manual testing or full user-specific batch jobs.

Usage:
    python scripts/run_all_tasks.py [user_email]

Environment Variables:
    DEFAULT_EMAIL           → fallback user email if not provided as argument
    SLEEP_BETWEEN_RUNS      → delay (in seconds) between each category (default: 2)
"""

import os
import sys
import time
import logging
from dotenv import load_dotenv
from scripts.run_generation_pipeline import run_pipeline

# Load .env
load_dotenv()

# Logger setup
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOG_FILE = os.path.join(ROOT_DIR, "scheduler", "logs", "run_all_tasks.log")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="📋 %(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()],
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("run_all_tasks")

# Categories to process
CATEGORIES = ["motivation", "success", "life", "inspiration", "sad"]
DEFAULT_EMAIL = os.getenv("DEFAULT_EMAIL", "developer@sazm.in")
SLEEP_BETWEEN = int(os.getenv("SLEEP_BETWEEN_RUNS", "2"))

def run_all_categories(user_email: str) -> None:
    """
    Generate reels for all categories for a given user.

    Args:
        user_email (str): Target user email/username.
    """
    user_email = user_email.strip().lower()
    logger.info(f"🚀 Starting batch reel generation for user: {user_email}")

    for i, category in enumerate(CATEGORIES, 1):
        try:
            logger.info(f"[{i}/{len(CATEGORIES)}] 🎬 Generating: {category}")
            result = run_pipeline(category, user_email)
            if result:
                logger.info(f"✅ {category.capitalize()} reel created at: {result}")
            else:
                logger.warning(f"⚠️  Reel generation failed for: {category}")
        except Exception as e:
            logger.exception(f"❌ Exception during generation for '{category}': {e}")

        if i < len(CATEGORIES):
            time.sleep(SLEEP_BETWEEN)

    logger.info(f"🏁 Completed all categories for: {user_email}")

if __name__ == "__main__":
    try:
        user_arg = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_EMAIL
        run_all_categories(user_arg)
    except Exception as e:
        logger.exception(f"💥 Fatal error in run_all_tasks: {e}")
        sys.exit(1)

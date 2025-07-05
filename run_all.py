# File: run_all.py

"""
Batch runner to generate reels for all categories for a given user.
"""

import os
import time
import sys
import logging
from dotenv import load_dotenv
from run_pipeline import run_pipeline

# Load environment variables from .env
load_dotenv()

# Logger setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("run_all")

# Constants
CATEGORIES = ["motivation", "success", "life", "inspiration", "sad"]
DEFAULT_EMAIL = os.getenv("DEFAULT_EMAIL", "developer@sazm.in")
SLEEP_BETWEEN = int(os.getenv("SLEEP_BETWEEN_RUNS", "2"))  # Delay (seconds) between reels


def run_all_categories(user_name: str) -> None:
    """
    Generate reels for all defined categories for a given user.

    Args:
        user_name (str): Target user_name.
    """
    logger.info(f"🚀 Starting batch reel generation for user: {user_name}")

    for category in CATEGORIES:
        try:
            logger.info(f"🔹 Generating reel for category: {category}")
            result = run_pipeline(category, user_name)

            if result:
                logger.info(f"[✅] {category.capitalize()} reel saved at: {result}")
            else:
                logger.warning(f"[⚠️] Reel generation failed for: {category}")

        except Exception as e:
            logger.exception(f"[❌] Error generating reel for '{category}': {e}")

        time.sleep(SLEEP_BETWEEN)

    logger.info(f"✅ Finished processing all categories for user: {user_name}")


if __name__ == "__main__":
    try:
        user_arg = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_EMAIL
        run_all_categories(user_arg)
    except Exception as e:
        logger.exception(f"Fatal error in batch runner: {e}")
        sys.exit(1)

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
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("run_all")

# Constants
CATEGORIES = ["motivation", "success", "life", "inspiration", "sad"]
DEFAULT_USERNAME = os.getenv("DEFAULT_USERNAME", "demo")
SLEEP_BETWEEN = int(os.getenv("SLEEP_BETWEEN_RUNS", "2"))  # Delay (seconds) between reels


def run_all_categories(username: str) -> None:
    """
    Generate reels for all defined categories for a given user.

    Args:
        username (str): Target username.
    """
    logger.info(f"🚀 Starting batch reel generation for user: {username}")

    for category in CATEGORIES:
        try:
            logger.info(f"🔹 Generating reel for category: {category}")
            result = run_pipeline(category, username)

            if result:
                logger.info(f"[✅] {category.capitalize()} reel saved at: {result}")
            else:
                logger.warning(f"[⚠️] Reel generation failed for: {category}")

        except Exception as e:
            logger.exception(f"[❌] Error generating reel for '{category}': {e}")

        time.sleep(SLEEP_BETWEEN)

    logger.info(f"✅ Finished processing all categories for user: {username}")


if __name__ == "__main__":
    user_arg = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_USERNAME
    run_all_categories(user_arg)

# run_all.py

"""
Batch runner to generate reels for all categories for a given user.
"""

import os
import time
import sys
import logging
from dotenv import load_dotenv
from run_pipeline import run_pipeline

# Load environment variables
load_dotenv()

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("run_all")

# Constants
CATEGORIES = ["motivation", "success", "life", "inspiration", "sad"]
DEFAULT_USERNAME = os.getenv("DEFAULT_USERNAME", "demo")
SLEEP_BETWEEN = int(os.getenv("SLEEP_BETWEEN_RUNS", "2"))  # Delay between categories


def run_all_categories(username):
    """
    Run video generation for all categories for the specified user.
    """
    logger.info(f"🚀 Starting full batch reel generation for user: {username}")

    for category in CATEGORIES:
        try:
            logger.info(f"🔹 Processing: {category}")
            result = run_pipeline(category, username)

            if result:
                logger.info(f"[✅] {category.capitalize()} video generated: {result}")
            else:
                logger.warning(f"[⚠️] {category} video generation failed.")

        except Exception as e:
            logger.exception(f"[❌] Error processing '{category}': {e}")

        time.sleep(SLEEP_BETWEEN)

    logger.info(f"\n✅ All categories processed for user: {username}")


if __name__ == "__main__":
    user = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_USERNAME
    run_all_categories(user)

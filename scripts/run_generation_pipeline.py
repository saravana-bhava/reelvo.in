# File: scripts/run_generation_pipeline.py

"""
Pipeline entry point to generate a single Instagram reel
for a given category and user using create_video_for_category().

Usage:
    python scripts/run_generation_pipeline.py <category> [user_email]

Example:
    python scripts/run_generation_pipeline.py motivation demo
"""

import sys
import logging
from typing import Optional
from dotenv import load_dotenv
from utils.create_video import create_video_for_category

# Load environment variables
load_dotenv()

# Logging setup
logger = logging.getLogger("run_generation_pipeline")
logger.setLevel(logging.INFO)
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    formatter = logging.Formatter("📽️  %(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def run_pipeline(category: str, user_email: str = "demo") -> Optional[str]:
    """
    Runs the video generation pipeline for a specific category and user.

    Args:
        category (str): Theme of the reel (e.g., motivation, success).
        user_email (str): User identifier (email or slug).

    Returns:
        Optional[str]: Path to the generated video, or None if failed.
    """
    category = category.strip().lower()
    user_email = user_email.strip().lower()

    logger.info(f"⚙️  Starting pipeline → Category: {category} | User: {user_email}")
    try:
        result = create_video_for_category(category, user_email)
        if result:
            logger.info(f"✅ Successfully generated reel → {result}")
        else:
            logger.warning(f"❌ Video generation failed for category: {category}")
        return result
    except Exception as e:
        logger.exception(f"🔥 Pipeline error for {category}: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        print(__doc__)
        sys.exit(1)

    category_arg = sys.argv[1].strip()
    user_arg = sys.argv[2].strip() if len(sys.argv) == 3 else "demo"

    run_pipeline(category_arg, user_arg)

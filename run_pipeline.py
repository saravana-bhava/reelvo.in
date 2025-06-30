# File: run_pipeline.py

"""
Pipeline entry point to generate a single Instagram reel
for a given category and username using create_video_for_category().
"""

import sys
import logging
from create_video import create_video_for_category

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("run_pipeline")


def run_pipeline(category: str, username: str = "demo") -> str | None:
    """
    Runs the video generation pipeline for a specific category and user.

    Args:
        category (str): Theme of the reel (e.g., motivation, success).
        username (str): User identifier.

    Returns:
        str | None: Path to the generated video, or None if failed.
    """
    logger.info(f"⚙️ Starting pipeline for: {category.upper()} | User: {username}")
    try:
        result = create_video_for_category(category, username)
        if result:
            logger.info(f"[✅] Reel generated → {result}")
        else:
            logger.warning(f"[❌] Video generation failed for category: {category}")
        return result
    except Exception as e:
        logger.exception(f"[❌] Pipeline failed for {category}: {e}")
        return None


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        print("Usage: python run_pipeline.py <category> [username]")
        print("Example: python run_pipeline.py motivation demo")
        sys.exit(1)

    category_arg = sys.argv[1].lower()
    username_arg = sys.argv[2] if len(sys.argv) == 3 else "demo"

    run_pipeline(category_arg, username_arg)

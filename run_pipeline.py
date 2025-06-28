# run_pipeline.py

import sys
import logging
from create_video import create_video_for_category

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("run_pipeline")

def run_pipeline(category: str, username: str = "demo") -> str | None:
    logger.info(f"⚙️ Starting pipeline for: {category.upper()} | User: {username}")
    try:
        result = create_video_for_category(category, username)
        if result:
            logger.info(f"[✅] Reel generated → {result}")
        else:
            logger.warning(f"[❌] Video generation failed for {category}")
        return result
    except Exception as e:
        logger.exception(f"[❌] Pipeline failed: {e}")
        return None


if __name__ == "__main__":
    if len(sys.argv) not in [2, 3]:
        print("Usage: python run_pipeline.py <category> [username]")
        print("Example: python run_pipeline.py motivation demo")
    else:
        category = sys.argv[1].lower()
        username = sys.argv[2] if len(sys.argv) == 3 else "demo"
        run_pipeline(category, username)

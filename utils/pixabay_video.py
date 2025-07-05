# File: utils/pixabay_video.py

"""
Fetches a vertical video clip (1080x1920+, 5–60s) from Pixabay based on a keyword.
Avoids reused URLs and ensures video quality meets Instagram Reel specs.
"""

import os
import logging
import requests
from typing import Optional, Set
from dotenv import load_dotenv
from utils.video_utils import download_video

# Load environment variables
load_dotenv()

# Logger setup
logger = logging.getLogger("pixabay_video")
logging.basicConfig(level=logging.INFO)

PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY")
PIXABAY_API_URL = "https://pixabay.com/api/videos/"


def fetch_pixabay_video(
    theme: str,
    output_path: str,
    used_urls: Optional[Set[str]] = None,
    min_duration: int = 5,
    max_duration: int = 6
) -> Optional[str]:
    """
    Searches Pixabay for a vertical (1080x1920+) video matching the theme.

    Args:
        theme (str): Category keyword like 'motivation' or 'life'.
        output_path (str): Where the selected video will be saved.
        used_urls (set): Set of URLs already used in this reel.
        min_duration (int): Minimum duration in seconds.
        max_duration (int): Maximum duration in seconds.

    Returns:
        str | None: Downloaded URL (added to used_urls), or None on failure.
    """
    if not PIXABAY_API_KEY:
        logger.error("[❌] Missing PIXABAY_API_KEY in .env")
        return None

    if used_urls is None:
        used_urls = set()

    logger.info(f"[🌐] Searching Pixabay for vertical videos: '{theme}'")

    try:
        response = requests.get(
            PIXABAY_API_URL,
            params={
                "key": PIXABAY_API_KEY,
                "q": theme,
                "video_type": "film",
                "orientation": "vertical",
                "per_page": 40
            },
            timeout=10
        )
        response.raise_for_status()
        hits = response.json().get("hits", [])

        logger.info(f"[ℹ️] Found {len(hits)} results on Pixabay.")

        for result in hits:
            duration = result.get("duration", 0)
            if not (min_duration <= duration <= max_duration):
                continue

            video_options = result.get("videos", {})
            for quality in ["large", "medium", "small", "tiny"]:
                video = video_options.get(quality)
                if not video:
                    continue

                url = video.get("url")
                width = video.get("width")
                height = video.get("height")

                if (
                    url
                    and url not in used_urls
                    and width >= 1080
                    and height >= 1920
                ):
                    logger.info(f"[🎞️] Candidate: {url} ({width}x{height}, {duration}s, {quality})")

                    success = download_video(
                        url,
                        output_path,
                        min_duration=min_duration,
                        max_duration=max_duration
                    )
                    if success:
                        used_urls.add(url)
                        logger.info(f"[✅] Saved to {output_path}")
                        return url
                    else:
                        logger.warning("[⚠️] Download failed, trying next...")

        logger.warning("[⚠️] No valid vertical 1080x1920+ video found on Pixabay.")
        return None

    except requests.exceptions.RequestException as e:
        logger.error(f"[❌] Pixabay API request failed: {e}")
    except Exception as e:
        logger.exception(f"[❌] Unexpected error during Pixabay fetch: {e}")

    return None


# CLI support
if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python utils/pixabay_video.py <theme> <output_path>")
        sys.exit(1)

    theme = sys.argv[1]
    output = sys.argv[2]

    result = fetch_pixabay_video(theme, output)
    if result:
        print(f"✅ Downloaded from: {result}")
    else:
        print("❌ No suitable video found.")

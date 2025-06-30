# File: utils/pexels_video.py

"""
Fetches a portrait video clip (1080x1920, 5–60s) from Pexels based on a category keyword.
Avoids reusing video URLs stored in `used_urls` during a session.
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
logger = logging.getLogger("pexels_video")
logging.basicConfig(level=logging.INFO)

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
HEADERS_PEXELS = {"Authorization": PEXELS_API_KEY}


def fetch_pexels_video(
    category: str,
    output_path: str,
    used_urls: Optional[Set[str]] = None,
    min_duration: int = 5,
    max_duration: int = 6
) -> Optional[str]:
    """
    Fetches a suitable 1080x1920 portrait video from Pexels matching the category.

    Args:
        category (str): Search keyword like "motivation", "life", etc.
        output_path (str): Where to save the downloaded video.
        used_urls (set): URLs already used in this reel session.
        min_duration (int): Minimum duration allowed in seconds.
        max_duration (int): Maximum duration allowed in seconds.

    Returns:
        str | None: Selected video URL, or None if no suitable clip found.
    """
    if not PEXELS_API_KEY:
        logger.error("[❌] Pexels API key not configured in .env")
        return None

    if used_urls is None:
        used_urls = set()

    logger.info(f"[🔎] Searching Pexels for category: '{category}'")

    try:
        response = requests.get(
            "https://api.pexels.com/videos/search",
            headers=HEADERS_PEXELS,
            params={
                "query": category,
                "orientation": "portrait",
                "per_page": 30
            },
            timeout=10
        )
        response.raise_for_status()
        videos = response.json().get("videos", [])
    except Exception as e:
        logger.warning(f"[❌] Failed to fetch from Pexels: {e}")
        return None

    for video in videos:
        duration = video.get("duration", 0)
        if duration < min_duration:
            continue

        for file in video.get("video_files", []):
            url = file.get("link")
            width = file.get("width")
            height = file.get("height")

            if (
                url and width == 1080 and height == 1920
                and url not in used_urls
            ):
                logger.info(f"[🎞️] Candidate found: {url} ({duration}s)")

                success = download_video(
                    url, output_path,
                    min_duration=min_duration,
                    max_duration=max_duration
                )

                if success:
                    used_urls.add(url)
                    logger.info(f"[✅] Downloaded successfully → {output_path}")
                    return url
                else:
                    logger.warning("[⚠️] Download failed, trying next...")

    logger.warning("[⚠️] No valid 1080x1920 portrait video found.")
    return None

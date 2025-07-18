# File: utils/pexels_video.py

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
PEXELS_API_URL = "https://api.pexels.com/videos/search"

HEADERS = {
    "Authorization": PEXELS_API_KEY
}


def fetch_pexels_video(
    theme: str,
    output_path: str,
    used_video_ids: Optional[Set[int]] = None,
    min_duration: int = 5,
    max_duration: int = 6
) -> Optional[str]:
    """
    Searches Pexels for a vertical (1080x1920+) video matching the theme.

    Args:
        theme (str): e.g. "inspiration", "love", etc.
        output_path (str): Path to save the downloaded clip.
        used_video_ids (set): Set of previously used video IDs to avoid repeats.
        min_duration (int): Minimum video duration in seconds.
        max_duration (int): Maximum video duration in seconds.

    Returns:
        str | None: URL of downloaded video, or None if none found.
    """
    if not PEXELS_API_KEY:
        logger.error("[❌] Missing PEXELS_API_KEY in .env")
        return None

    if used_video_ids is None:
        used_video_ids = set()

    logger.info(f"[🌐] Searching Pexels for vertical videos: '{theme}'")

    try:
        response = requests.get(
            PEXELS_API_URL,
            headers=HEADERS,
            params={
                "query": theme,
                "orientation": "portrait",
                "per_page": 40
            },
            timeout=10
        )
        response.raise_for_status()
        results = response.json().get("videos", [])
        logger.info(f"[ℹ️] Found {len(results)} results on Pexels.")

        for result in results:
            video_id = result.get("id")
            duration = result.get("duration", 0)

            if not video_id:
                continue

            if video_id in used_video_ids:
                logger.debug(f"[⏩] Skipping previously used video ID: {video_id}")
                continue

            if not (min_duration <= duration <= max_duration):
                logger.debug(f"[⏩] Skipping video {video_id} due to duration {duration}s")
                continue

            used_video_ids.add(video_id)  # ✅ Add early to avoid multiple attempts

            files = result.get("video_files", [])

            for file in files:
                width = file.get("width", 0)
                height = file.get("height", 0)
                link = file.get("link")

                if not link:
                    continue

                if width >= 1080 and height >= 1920:
                    logger.info(f"[🎞️] Trying: {link} ({width}x{height}, {duration}s)")

                    success = download_video(
                        link,
                        output_path,
                        min_duration=min_duration,
                        max_duration=max_duration
                    )
                    if success:
                        logger.info(f"[✅] Saved to {output_path}")
                        return link
                    else:
                        logger.warning("[⚠️] Download failed, trying next file...")
                else:
                    logger.debug(f"[🔻] Skipped low-res file: {width}x{height}")

        logger.warning("[⚠️] No valid vertical video found on Pexels.")
        return None

    except requests.exceptions.RequestException as e:
        logger.error(f"[❌] Pexels API request failed: {e}")
    except Exception as e:
        logger.exception(f"[❌] Unexpected error during Pexels fetch: {e}")

    return None


# CLI test mode
if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python utils/pexels_video.py <theme> <output_path>")
        sys.exit(1)

    theme = sys.argv[1]
    output_path = sys.argv[2]

    downloaded = fetch_pexels_video(theme, output_path, used_video_ids=set())
    if downloaded:
        print(f"✅ Downloaded from: {downloaded}")
    else:
        print("❌ No suitable video found.")

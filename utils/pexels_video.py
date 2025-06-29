# utils/pexels_video.py

"""
Fetches a portrait video clip (1080x1920, 5–60s) from Pexels based on a category keyword.
Avoids reusing video URLs stored in `used_urls` during a session.
"""

import os
import requests
from typing import Optional, Set
from dotenv import load_dotenv
from utils.video_utils import download_video

# Load environment variables
load_dotenv()

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
    Fetches a suitable 1080x1920 video clip from Pexels matching the category.
    Returns the selected video URL or None if not found.

    Args:
        category: Search keyword like "motivation", "life", etc.
        output_path: Where to save the downloaded video.
        used_urls: Set of video URLs already used in the current reel.
        min_duration: Minimum allowed duration in seconds.
        max_duration: Maximum allowed duration in seconds.
    """
    if not PEXELS_API_KEY:
        print("[❌] Pexels API key not configured in .env")
        return None

    if used_urls is None:
        used_urls = set()

    print(f"[🔎] Querying Pexels for '{category}' portrait videos...")

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
        print(f"[❌] Failed to fetch from Pexels: {e}")
        return None

    for video in videos:
        duration = video.get("duration", 0)
        if not (min_duration <= duration):
            continue

        for file in video.get("video_files", []):
            url = file.get("link")
            width, height = file.get("width"), file.get("height")

            if (
                width == 1080 and height == 1920 and url
                and url not in used_urls
            ):
                print(f"[🎞️] Found candidate: {url} ({duration}s)")

                success = download_video(
                    url, output_path,
                    min_duration=min_duration,
                    max_duration=max_duration
                )

                if success:
                    print(f"[✅] Downloaded: {output_path}")
                    return url  # ← Return this so caller can add it to used_urls
                else:
                    print("[⚠️] Download failed, trying next...")

    print("[⚠️] No valid 1080x1920 portrait video found within 5–60 seconds.")
    return None

# utils/pexels_video.py

"""
Fetches a portrait video clip (1080x1920, 8–12s) from Pexels based on a category keyword.
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


def try_pexels_fallback(
    category: str,
    output_path: str,
    used_urls: Optional[Set[str]] = None,
    min_duration: int = 8,
    max_duration: int = 12
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

    used_urls = used_urls or set()
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
        if not (min_duration <= duration <= max_duration):
            continue

        for file in video.get("video_files", []):
            url = file.get("link")
            width, height = file.get("width"), file.get("height")

            if width == 1080 and height == 1920 and url and url not in used_urls:
                print(f"[🎞️] Found candidate: {url} ({duration}s)")
                if download_video(url, output_path, min_duration, max_duration):
                    used_urls.add(url)
                    print(f"[✅] Video downloaded to: {output_path}")
                    return url
                else:
                    print("[⚠️] Download failed, trying next...")

    print("[⚠️] No valid 1080x1920 portrait video found within 8–12 seconds.")
    return None

# utils/pixabay_video.py

"""
Fetches a vertical video clip (1080x1920, 5–60s) from Pixabay based on a keyword.
Avoids reused URLs and ensures video quality meets Instagram Reel specs.
"""

import os
import requests
from typing import Optional, Set
from dotenv import load_dotenv
from utils.video_utils import download_video

# Load environment variables
load_dotenv()

PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY")
PIXABAY_API_URL = "https://pixabay.com/api/videos/"


def fetch_pixabay_video(
    theme: str,
    output_path: str,
    used_urls: Optional[Set[str]] = None,
    min_duration: int = 5,
    max_duration: int = 60
) -> Optional[str]:
    """
    Searches Pixabay for a portrait (1080x1920) video matching the theme.
    Returns the selected video URL or None if no match found.

    Args:
        theme: Category keyword like 'motivation' or 'life'
        output_path: Where the selected video will be saved
        used_urls: Set of URLs already used in this reel
        min_duration: Minimum duration in seconds
        max_duration: Maximum duration in seconds
    """
    if not PIXABAY_API_KEY:
        raise EnvironmentError("[❌] Missing PIXABAY_API_KEY in .env")

    if used_urls is None:
        used_urls = set()

    print(f"[🌐] Searching Pixabay for '{theme}' vertical videos...")

    try:
        response = requests.get(
            PIXABAY_API_URL,
            params={
                "key": PIXABAY_API_KEY,
                "q": theme,
                "video_type": "film",
                "orientation": "vertical",
                "per_page": 30
            },
            timeout=10
        )
        response.raise_for_status()
        hits = response.json().get("hits", [])

        if not hits:
            print("[⚠️] No results from Pixabay.")
            return None

        for result in hits:
            duration = result.get("duration", 0)
            if not (min_duration <= duration <= max_duration):
                continue

            for quality in ["large", "medium", "small", "tiny"]:
                video = result.get("videos", {}).get(quality)
                if not video:
                    continue

                url = video.get("url")
                width, height = video.get("width"), video.get("height")

                if url and url not in used_urls and width == 1080 and height == 1920:
                    print(f"[🎞️] Candidate found: {url} ({duration}s, {quality})")

                    success = download_video(url, output_path, min_duration, max_duration)
                    if success:
                        print(f"[✅] Video saved → {output_path}")
                        return url  # Return to caller to track in used_urls
                    else:
                        print("[⚠️] Download failed, continuing...")

        print("[⚠️] No valid 1080x1920 clip found on Pixabay.")
        return None

    except Exception as e:
        print(f"[❌] Pixabay API error: {e}")
        return None

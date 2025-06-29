# File: utils/fetch_bgm_from_pixabay.py

import os
import logging
import requests
from urllib.parse import urlencode
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("pixabay_bgm")

PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY")
PIXABAY_MUSIC_ENDPOINT = "https://pixabay.com/api/sounds/"

def fetch_bgm_from_pixabay(query: str, duration: float = 30.0) -> str | None:
    """Fetch suitable BGM track from Pixabay based on English query."""
    if not PIXABAY_API_KEY:
        logger.error("[❌] Pixabay API key not set")
        return None

    params = {
        "key": PIXABAY_API_KEY,
        "q": query,
        "min_duration": int(duration - 5),
        "max_duration": int(duration + 5),
        "per_page": 10,
        "safesearch": "true",
        "order": "popular"
    }

    try:
        response = requests.get(PIXABAY_MUSIC_ENDPOINT, params=params, timeout=10)
        if response.status_code != 200:
            logger.error(f"[❌] Pixabay error: {response.status_code} - {response.text}")
            return None

        try:
            data = response.json()
        except Exception as e:
            logger.error(f"[❌] Failed to decode JSON: {e}")
            logger.debug(f"Raw response: {response.text}")
            return None

        hits = data.get("hits", [])
        for track in hits:
            url = track.get("audio")
            if url:
                logger.info(f"[🎵] Fetched Pixabay BGM: {track.get('id')} - {url}")
                return url

        logger.warning("[⚠️] No suitable BGM track found.")
        return None

    except Exception as e:
        logger.exception(f"[❌] Failed to fetch BGM: {e}")
        return None

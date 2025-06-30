# File: utils/freesound_bgm.py

import os
import requests
import logging
from urllib.parse import quote
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

FREESOUND_API_KEY = os.getenv("FREESOUND_API_KEY")
FREESOUND_API_URL = "https://freesound.org/apiv2/search/text/"
logger = logging.getLogger("freesound_bgm")

HEADERS = {
    "Authorization": f"Token {FREESOUND_API_KEY}"
}

def search_freesound(query: str) -> str | None:
    """
    Search Freesound.org for background music by keyword and return best match preview MP3.
    """
    if not FREESOUND_API_KEY:
        logger.warning("[⚠️] FREESOUND_API_KEY not set. Cannot fetch BGM.")
        return None

    search_url = (
        f"{FREESOUND_API_URL}?query=music+{quote(query)}"
        f"&filter=duration:[5 TO 30]"
        f"&fields=name,previews,license,duration,download"
        f"&sort=score+desc&page_size=5"
    )

    logger.info(f"[🔍] Searching Freesound for: {query}")
    try:
        resp = requests.get(search_url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        results = resp.json().get("results", [])
        if not results:
            logger.warning(f"[❌] No results found for: {query}")
            return None

        preview_url = results[0]["previews"]["preview-hq-mp3"]
        logger.info(f"[🎧] Found preview MP3: {preview_url}")
        return preview_url
    except Exception as e:
        logger.warning(f"[❌] Error while searching Freesound: {e}")
        return None

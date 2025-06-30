# File: utils/freesound_bgm.py

import os
import requests
import logging
from urllib.parse import quote
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

FREESOUND_API_KEY = os.getenv("FREESOUND_API_KEY")
FREESOUND_API_URL = "https://freesound.org/apiv2/search/text/"
logger = logging.getLogger("freesound_bgm")

HEADERS = {
    "Authorization": f"Token {FREESOUND_API_KEY}"
}


def search_freesound(query: str) -> str | None:
    """
    Search Freesound.org for background music using a keyword,
    and return the URL to a high-quality preview MP3 if found.

    Args:
        query (str): The keyword to search for (e.g., "inspiration").

    Returns:
        str | None: Preview MP3 URL or None if not found or error.
    """
    if not FREESOUND_API_KEY:
        logger.warning("[⚠️] FREESOUND_API_KEY not set. Cannot fetch BGM.")
        return None

    # Construct Freesound search URL with filters and fields
    search_url = (
        f"{FREESOUND_API_URL}?query=music+{quote(query)}"
        f"&filter=duration:[5 TO 30]"
        f"&fields=name,previews,license,duration,download"
        f"&sort=score+desc&page_size=5"
    )

    logger.info(f"[🔍] Searching Freesound for: '{query}'")

    try:
        resp = requests.get(search_url, headers=HEADERS, timeout=10)
        resp.raise_for_status()

        results = resp.json().get("results", [])
        if not results:
            logger.warning(f"[❌] No results found for: '{query}'")
            return None

        # Use the highest scored result
        preview_url = results[0].get("previews", {}).get("preview-hq-mp3")
        if preview_url:
            logger.info(f"[🎧] Found preview MP3: {preview_url}")
            return preview_url
        else:
            logger.warning("[⚠️] Preview MP3 not found in response.")

    except Exception as e:
        logger.warning(f"[❌] Freesound API error: {e}")

    return None

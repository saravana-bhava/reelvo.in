# File: utils/freesound_bgm.py

import os
import logging
import requests
import string
from urllib.parse import quote
from typing import Optional
from dotenv import load_dotenv

# Configure logging before anything else
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("freesound_bgm")

# Load environment variables from .env
load_dotenv()

FREESOUND_API_KEY = os.getenv("FREESOUND_API_KEY")
FREESOUND_API_URL = "https://freesound.org/apiv2/search/text/"

HEADERS = {
    "Authorization": f"Token {FREESOUND_API_KEY}"
}


def sanitize_filename(name: str) -> str:
    """Remove unsafe characters from file names."""
    return ''.join(c for c in name if c in string.ascii_letters + string.digits + "_").lower()


def search_freesound(query: str, language: str = "en") -> Optional[str]:
    """
    Search Freesound.org for background music using a keyword,
    and return the path to a high-quality preview MP3 if found.

    Args:
        query (str): Keyword for search (e.g., 'success', 'motivation').
        language (str): Language hint for filename suffix ('en', 'hi').

    Returns:
        Optional[str]: Downloaded MP3 file path or None if failed.
    """
    if not FREESOUND_API_KEY:
        logger.warning("[⚠️] FREESOUND_API_KEY not set. Skipping BGM.")
        return None

    encoded_query = quote(f"music {query}")
    search_url = (
        f"{FREESOUND_API_URL}?query={encoded_query}"
        f"&filter=duration:[5 TO 30]"
        f"&fields=name,previews,license,duration,download"
        f"&sort=score+desc&page_size=5"
    )

    logger.info(f"[🔍] Searching Freesound for: '{query}' (lang={language})")

    try:
        response = requests.get(search_url, headers=HEADERS, timeout=10)
        response.raise_for_status()

        results = response.json().get("results", [])
        if not results:
            logger.warning(f"[❌] No Freesound results for: '{query}'")
            return None

        top_result = results[0]
        previews = top_result.get("previews", {})

        preview_url = (
            previews.get("preview-hq-mp3") or
            previews.get("preview-lq-mp3") or
            None
        )

        if not preview_url:
            logger.warning("[⚠️] No MP3 preview available in top result.")
            return None

        os.makedirs("cache/bgm", exist_ok=True)
        base_name = sanitize_filename(query)
        filename = f"{base_name}_{language}.mp3"
        dest_path = os.path.join("cache/bgm", filename)

        if os.path.exists(dest_path):
            logger.info(f"[📦] Using cached BGM: {dest_path}")
            return dest_path

        logger.info(f"[⬇️] Downloading BGM → {dest_path}")
        with requests.get(preview_url, stream=True, timeout=15) as r:
            r.raise_for_status()
            with open(dest_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        logger.info(f"[✅] Downloaded BGM saved: {dest_path}")
        return dest_path

    except requests.RequestException as e:
        logger.warning(f"[❌] Freesound API error: {e}")
    except Exception as e:
        logger.warning(f"[❌] Unexpected Freesound error: {e}")

    return None


# CLI for manual testing
if __name__ == "__main__":
    import sys
    if len(sys.argv) not in (2, 3):
        print("Usage: python utils/freesound_bgm.py <query> [language]")
    else:
        q = sys.argv[1]
        lang = sys.argv[2] if len(sys.argv) == 3 else "en"
        result = search_freesound(q, language=lang)
        print(f"Result: {result}")

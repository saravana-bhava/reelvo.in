# File: utils/fetch_bgm.py

import os
import re
import logging
import requests
import string

from utils.freesound_bgm import search_freesound
from utils.translate_text import translate_to_english

logger = logging.getLogger("bgm_fetcher")

CACHE_DIR = "cache/bgm"
os.makedirs(CACHE_DIR, exist_ok=True)


def sanitize_filename(name: str) -> str:
    """Sanitize a string to be a safe lowercase filename."""
    return ''.join(c for c in name if c in string.ascii_letters + string.digits + "_").lower()


def download_bgm_from_url(url: str, dest_path: str) -> str | None:
    """
    Download an audio file from a URL and save it locally.

    Args:
        url (str): Direct link to the MP3 audio.
        dest_path (str): Where to save the downloaded file.

    Returns:
        str | None: Path to the saved file, or None if failed.
    """
    try:
        logger.info(f"[🌐] Downloading BGM from: {url}")
        response = requests.get(url, stream=True, timeout=15)
        if response.status_code == 200:
            with open(dest_path, 'wb') as f:
                for chunk in response.iter_content(1024 * 64):
                    f.write(chunk)
            logger.info(f"[✅] BGM saved to: {dest_path}")
            return dest_path
        else:
            logger.warning(f"[⚠️] Failed to download BGM. Status code: {response.status_code}")
    except Exception as e:
        logger.warning(f"[❌] Exception during BGM download: {e}")
    return None


def fetch_bgm(script_text: str, language: str = "en", fallback_category: str | None = None) -> str | None:
    """
    Fetch background music matching script content.

    Args:
        script_text (str): Script content to extract keywords from.
        language (str): Language of the script ("en" or "hi").
        fallback_category (str | None): Optional fallback music category.

    Returns:
        str | None: Path to the local MP3 file or None if not found.
    """
    # Translate script to English if needed
    if language != "en":
        try:
            logger.info("[🌐] Translating script to English for BGM matching...")
            script_text = translate_to_english(script_text)
        except Exception:
            logger.warning("[⚠️] Translation failed. Proceeding with raw script.")

    # Extract long English words (keyword candidates)
    words = re.findall(r'\b\w+\b', script_text.lower())
    long_words = [w for w in words if len(w) > 5 and w.isascii()]
    keyword = long_words[0] if long_words else "inspiration"
    safe_keyword = sanitize_filename(keyword)

    logger.info(f"[🔍] Extracted BGM keyword candidates: {long_words}")
    logger.info(f"[🎵] Using keyword: '{keyword}' (safe: '{safe_keyword}')")

    cached_path = os.path.join(CACHE_DIR, f"{safe_keyword}.mp3")
    if os.path.exists(cached_path):
        logger.info(f"[💾] Using cached BGM: {cached_path}")
        return cached_path

    # Try Freesound
    try:
        bgm_url_or_path = search_freesound(keyword)
        if bgm_url_or_path:
            if bgm_url_or_path.startswith("http"):
                return download_bgm_from_url(bgm_url_or_path, cached_path)
            elif os.path.exists(bgm_url_or_path):
                os.rename(bgm_url_or_path, cached_path)
                logger.info(f"[✅] Renamed local BGM to cache: {cached_path}")
                return cached_path
    except Exception as e:
        logger.warning(f"[❌] Freesound lookup failed: {e}")

    # Fallback to local category music
    if fallback_category:
        fallback_path = os.path.join("assets", "music", f"{fallback_category}.mp3")
        if os.path.exists(fallback_path):
            logger.info(f"[🎼] Using fallback category BGM: {fallback_path}")
            return fallback_path

    logger.warning("[⚠️] No suitable BGM found or fallback failed.")
    return None

# File: utils/fetch_bgm.py

import os
import re
import logging
import requests
import string
from typing import Optional

from utils.freesound_bgm import search_freesound
from utils.translate_text import translate_to_english

logger = logging.getLogger("bgm_fetcher")

CACHE_DIR = os.path.join("cache", "bgm")
os.makedirs(CACHE_DIR, exist_ok=True)


def sanitize_filename(name: str) -> str:
    """Sanitize a string to be a safe lowercase filename."""
    return ''.join(c for c in name if c in string.ascii_letters + string.digits + "_").lower()


def download_bgm_from_url(url: str, dest_path: str) -> Optional[str]:
    """
    Download an audio file from a URL and save it locally.

    Args:
        url (str): Direct link to the MP3 audio.
        dest_path (str): Where to save the downloaded file.

    Returns:
        Optional[str]: Path to the saved file, or None if failed.
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
    except requests.RequestException as e:
        logger.warning(f"[❌] Request error during BGM download: {e}")
    except Exception as e:
        logger.warning(f"[❌] Unexpected error during BGM download: {e}")
    return None


def fetch_bgm(script_text: str, language: str = "en", fallback_category: Optional[str] = None) -> Optional[str]:
    """
    Fetch background music matching script content.

    Args:
        script_text (str): Script content to extract keywords from.
        language (str): Language of the script ("en" or "hi").
        fallback_category (Optional[str]): Optional fallback music category.

    Returns:
        Optional[str]: Path to the local MP3 file or None if not found.
    """
    # Translate to English if needed
    original_text = script_text
    if language != "en":
        try:
            logger.info("[🌐] Translating script to English for BGM matching...")
            script_text = translate_to_english(script_text)
        except Exception as e:
            logger.warning(f"[⚠️] Translation failed: {e}. Proceeding with raw script.")
            script_text = original_text

    # Extract long words (keyword candidates)
    words = re.findall(r'\b\w+\b', script_text.lower())
    long_words = [w for w in words if len(w) > 5 and w.isascii()]
    keyword = long_words[0] if long_words else "inspiration"
    safe_keyword = sanitize_filename(keyword)

    logger.info(f"[🔍] Extracted BGM keyword candidates: {long_words}")
    logger.info(f"[🎵] Using keyword: '{keyword}' (safe: '{safe_keyword}')")

    # Append language to filename
    suffix = "_hi" if language == "hi" else "_en"
    cache_filename = f"{safe_keyword}{suffix}.mp3"
    cached_path = os.path.join(CACHE_DIR, cache_filename)

    if os.path.exists(cached_path):
        logger.info(f"[💾] Using cached BGM: {cached_path}")
        return cached_path

    # Try Freesound
    try:
        bgm_url_or_path = search_freesound(keyword, language=language)
        if bgm_url_or_path:
            if bgm_url_or_path.startswith("http"):
                return download_bgm_from_url(bgm_url_or_path, cached_path)
            elif os.path.exists(bgm_url_or_path):
                try:
                    os.rename(bgm_url_or_path, cached_path)
                    logger.info(f"[✅] Renamed local BGM to cache: {cached_path}")
                    return cached_path
                except Exception as e:
                    logger.warning(f"[⚠️] Failed to move local BGM file: {e}")
                    return bgm_url_or_path
    except Exception as e:
        logger.warning(f"[❌] Freesound lookup failed: {e}")

    # Fallback music
    if fallback_category:
        fallback_path = os.path.join("assets", "music", f"{fallback_category}.mp3")
        if os.path.exists(fallback_path):
            logger.info(f"[🎼] Using fallback category BGM: {fallback_path}")
            return fallback_path

    logger.warning("[⚠️] No suitable BGM found or fallback failed.")
    return None

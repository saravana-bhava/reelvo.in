# File: utils/fetch_bgm.py

import os
import re
import logging
import requests
import string
from typing import Optional

from utils.freesound_bgm import search_freesound
from utils.translate_text import translate_to_english

# Setup
logger = logging.getLogger("bgm_fetcher")
logging.basicConfig(level=logging.INFO)

CACHE_DIR = os.path.join("cache", "bgm")
os.makedirs(CACHE_DIR, exist_ok=True)


def sanitize_filename(name: str) -> str:
    """Sanitize a string to a safe lowercase filename."""
    return ''.join(c for c in name if c in string.ascii_letters + string.digits + "_").lower()


def download_bgm_from_url(url: str, dest_path: str) -> Optional[str]:
    """Download an audio file from a URL and save it locally."""
    try:
        logger.info(f"[🌐] Downloading BGM from: {url}")
        response = requests.get(url, stream=True, timeout=15)
        response.raise_for_status()

        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(1024 * 64):
                f.write(chunk)

        logger.info(f"[✅] BGM saved to: {dest_path}")
        return dest_path

    except requests.RequestException as e:
        logger.warning(f"[❌] Request error during BGM download: {e}")
    except Exception as e:
        logger.warning(f"[❌] Unexpected error during BGM download: {e}")

    return None


def fetch_bgm(
    script_text: str,
    language: str = "en",
    fallback_category: Optional[str] = None
) -> Optional[str]:
    """Fetch background music matching the script content."""
    original_text = script_text

    if language != "en":
        try:
            logger.info("[🌐] Translating script to English for BGM match...")
            script_text = translate_to_english(script_text)
        except Exception as e:
            logger.warning(f"[⚠️] Translation failed: {e}. Using original script.")
            script_text = original_text

    words = re.findall(r'\b\w+\b', script_text.lower())
    long_words = [w for w in words if len(w) > 5 and w.isascii()]
    keyword = long_words[0] if long_words else "inspiration"
    safe_keyword = sanitize_filename(keyword)

    logger.info(f"[🔍] BGM keyword candidates: {long_words}")
    logger.info(f"[🎵] Using keyword: '{keyword}' (safe: '{safe_keyword}')")

    suffix = "_hi" if language == "hi" else "_en"
    cache_filename = f"{safe_keyword}{suffix}.mp3"
    cached_path = os.path.join(CACHE_DIR, cache_filename)

    if os.path.exists(cached_path):
        logger.info(f"[💾] Using cached BGM: {cached_path}")
        return cached_path

    try:
        bgm_url_or_path = search_freesound(keyword, language=language)

        if bgm_url_or_path:
            if bgm_url_or_path.startswith("http"):
                return download_bgm_from_url(bgm_url_or_path, cached_path)
            elif os.path.exists(bgm_url_or_path):
                try:
                    os.rename(bgm_url_or_path, cached_path)
                    logger.info(f"[✅] Renamed BGM to cache: {cached_path}")
                    return cached_path
                except Exception as e:
                    logger.warning(f"[⚠️] Failed to move BGM file: {e}")
                    return bgm_url_or_path

    except Exception as e:
        logger.warning(f"[❌] Freesound lookup failed for keyword '{keyword}': {e}")

    # Fallback music
    if fallback_category:
        fallback_path = os.path.join("assets", "music", f"{fallback_category}.mp3")
        if os.path.exists(fallback_path):
            logger.info(f"[🎼] Using fallback BGM for category '{fallback_category}': {fallback_path}")
            return fallback_path
        else:
            logger.warning(f"[⚠️] Fallback category file not found: {fallback_path}")

    logger.warning("[⚠️] No suitable BGM found or fallback failed.")
    return None

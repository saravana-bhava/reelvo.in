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


def sanitize_filename(name):
    """Sanitize keyword to be a safe filename."""
    return ''.join(c for c in name if c in string.ascii_letters + string.digits + "_").lower()


def download_bgm_from_url(url, dest_path):
    """Download audio file from remote URL to local path."""
    try:
        logger.info(f"[🌐] Downloading BGM from: {url}")
        response = requests.get(url, stream=True, timeout=15)
        if response.status_code == 200:
            with open(dest_path, 'wb') as f:
                for chunk in response.iter_content(1024 * 64):
                    f.write(chunk)
            logger.info(f"[✅] BGM downloaded and saved to: {dest_path}")
            return dest_path
        else:
            logger.warning(f"[⚠️] Failed to download BGM. Status code: {response.status_code}")
    except Exception as e:
        logger.warning(f"[❌] Exception during BGM download: {e}")
    return None


def fetch_bgm(script_text, language="en", fallback_category=None):
    """
    Fetch background music matching script keywords.
    Prioritizes English keywords; auto-translates if needed.
    Uses local cache if available.
    """
    # Translate if needed
    if language != "en":
        try:
            logger.info("[🌐] Translating script for BGM keyword extraction...")
            script_text = translate_to_english(script_text)
        except Exception:
            logger.warning("[⚠️] Translation for BGM failed. Using raw script.")

    # Extract long ASCII keywords
    words = re.findall(r'\b\w+\b', script_text.lower())
    long_words = [w for w in words if len(w) > 5 and w.isascii()]
    keyword = long_words[0] if long_words else "inspiration"
    safe_keyword = sanitize_filename(keyword)

    logger.info(f"[🔍] BGM keyword selected from long words: {long_words}")
    logger.info(f"[🎵] Checking BGM cache or fetching from Freesound: {keyword}")

    cached_path = os.path.join(CACHE_DIR, f"{safe_keyword}.mp3")
    if os.path.exists(cached_path):
        logger.info(f"[💾] Using cached BGM: {cached_path}")
        return cached_path

    try:
        bgm_url_or_path = search_freesound(keyword)

        if bgm_url_or_path:
            if bgm_url_or_path.startswith("http"):
                return download_bgm_from_url(bgm_url_or_path, cached_path)
            elif os.path.exists(bgm_url_or_path):
                os.rename(bgm_url_or_path, cached_path)
                logger.info(f"[✅] Cached BGM saved to: {cached_path}")
                return cached_path
    except Exception as e:
        logger.warning(f"[❌] Freesound search failed: {e}")

    if fallback_category:
        fallback_path = os.path.join("assets", f"{fallback_category}.mp3")
        if os.path.exists(fallback_path):
            logger.info(f"[🎵] Using fallback BGM: {fallback_path}")
            return fallback_path

    logger.warning("[⚠️] No valid BGM found. Skipping background music.")
    return None

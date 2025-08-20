# ================================================
# File:         utils/fetch_bgm.py
# Description:  Fetch background music from various sources
# Framework:    Flask + TailwindCSS
# Version:      1.0.0
# Last Updated: 20 August 2025
# Author:       Saravana Bhava
# Author URL:   https://SazM.in
# ================================================

import os
import re
import logging
import string
import requests
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

from utils.freesound_bgm import search_freesound
from utils.translate_text import translate_to_english
from utils.progress_tracker import update_progress

# Load .env
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=ROOT_DIR / ".env")

# Logger setup
logger = logging.getLogger("bgm_fetcher")
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO)

# Base directory (from environment)
BASE_DIR = Path(os.getenv("BASE_DIR", str(ROOT_DIR))).resolve()

# Directories
BGM_DIR = BASE_DIR / "cache" / "bgm"
BGM_DIR.mkdir(parents=True, exist_ok=True)

ASSETS_DIR = BASE_DIR / "assets" / "music"
DEFAULT_BGM = ASSETS_DIR / "default.mp3"
MAX_BGM_SIZE_MB = 20


def sanitize_filename(name: str) -> str:
    """
    Sanitize a string to a lowercase alphanumeric-safe filename.
    """
    allowed_chars = string.ascii_letters + string.digits + "_"
    return ''.join(c for c in name if c in allowed_chars).lower()


def download_bgm_from_url(url: str, dest_path: Path, task_id: Optional[str] = None) -> Optional[str]:
    """
    Download audio from a given URL and save it to the destination path.
    """
    try:
        logger.info(f"[🌐] Downloading BGM from: {url}")
        if task_id:
            update_progress(task_id, "🎵 Downloading music...", 30)

        response = requests.get(url, stream=True, timeout=15)
        response.raise_for_status()

        content_length = int(response.headers.get("Content-Length", 0))
        if content_length > MAX_BGM_SIZE_MB * 1024 * 1024:
            logger.warning(f"[⚠️] BGM file too large ({content_length} bytes), skipping.")
            return None

        with dest_path.open('wb') as f:
            for chunk in response.iter_content(1024 * 64):
                if chunk:
                    f.write(chunk)

        logger.info(f"[✅] BGM saved to: {dest_path}")
        if task_id:
            update_progress(task_id, "🎵 Music downloaded", 40)
        return str(dest_path)

    except requests.RequestException as e:
        logger.warning(f"[❌] Request error during BGM download: {e}")
    except Exception as e:
        logger.warning(f"[❌] Unexpected error during BGM download: {e}")

    return None


def fetch_bgm(
    script_text: str,
    language: str = "en",
    fallback_category: Optional[str] = None,
    force_download: bool = False,
    task_id: Optional[str] = None
) -> Optional[str]:
    """
    Fetch a background music track relevant to the script content.

    Attempts in order:
    1. Cached version.
    2. Download via freesound.
    3. Category fallback.
    4. Generic fallback.
    """
    original_text = script_text

    if task_id:
        update_progress(task_id, "🎵 Translating script...", 10)

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
    cached_path = BGM_DIR / cache_filename

    if cached_path.exists() and not force_download:
        logger.info(f"[💾] Using cached BGM: {cached_path}")
        if task_id:
            update_progress(task_id, "🎵 Using cached music", 40)
        return str(cached_path)

    try:
        if task_id:
            update_progress(task_id, f"🎵 Searching for music using keyword '{keyword}'", 20)

        bgm_url_or_path = search_freesound(keyword, language=language)

        if bgm_url_or_path:
            if bgm_url_or_path.startswith("http"):
                return download_bgm_from_url(bgm_url_or_path, cached_path, task_id)
            else:
                source_path = Path(bgm_url_or_path)
                if source_path.exists():
                    try:
                        source_path.rename(cached_path)
                        logger.info(f"[✅] Renamed BGM to cache: {cached_path}")
                        if task_id:
                            update_progress(task_id, "🎵 Music copied to cache", 40)
                        return str(cached_path)
                    except Exception as e:
                        logger.warning(f"[⚠️] Failed to move BGM file: {e}")
                        return str(source_path)

    except Exception as e:
        logger.warning(f"[❌] Freesound lookup failed for keyword '{keyword}': {e}")

    # Fallback to category
    if fallback_category:
        fallback_path = ASSETS_DIR / f"{fallback_category}.mp3"
        if fallback_path.exists():
            logger.info(f"[🎼] Using fallback BGM for category '{fallback_category}': {fallback_path}")
            if task_id:
                update_progress(task_id, "🎵 Using fallback category music", 40)
            return str(fallback_path)
        else:
            logger.warning(f"[⚠️] Fallback category file not found: {fallback_path}")

    # Final fallback to generic default
    if DEFAULT_BGM.exists():
        logger.info(f"[🎼] Using default fallback BGM: {DEFAULT_BGM}")
        if task_id:
            update_progress(task_id, "🎵 Using default fallback music", 40)
        return str(DEFAULT_BGM)

    logger.warning("[⚠️] No suitable BGM found or fallback failed.")
    if task_id:
        update_progress(task_id, "❌ No suitable BGM found", 40)
    return None

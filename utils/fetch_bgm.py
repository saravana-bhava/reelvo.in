# File: utils/fetch_bgm.py

import os
import logging
from dotenv import load_dotenv
from utils.fetch_bgm_from_freesound import fetch_bgm_from_freesound

# Load environment variables
load_dotenv()

# Configure logger
logger = logging.getLogger("bgm_fetcher")
logging.basicConfig(level=logging.INFO)

# Ensure BGM output directory exists
ASSETS_DIR = os.path.join("assets", "music")
os.makedirs(ASSETS_DIR, exist_ok=True)


def fetch_bgm(category: str) -> str:
    """
    Fetch background music for a given category using Freesound API.

    Args:
        category (str): The category name (e.g., 'motivation', 'success').

    Returns:
        str: Path to the downloaded MP3 file.

    Raises:
        Exception: If no BGM could be fetched from Freesound.
    """
    out_path = os.path.join(ASSETS_DIR, f"{category}.mp3")

    try:
        logger.info(f"[🎵] Fetching BGM from Freesound: {category}")
        if fetch_bgm_from_freesound(category, out_path):
            return out_path
        logger.error("[❌] Freesound BGM fetch failed.")
    except Exception as e:
        logger.exception(f"[❌] Error fetching BGM from Freesound: {e}")

    raise Exception("BGM fetch failed from Freesound.")

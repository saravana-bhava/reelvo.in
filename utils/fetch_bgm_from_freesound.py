# File: utils/fetch_bgm_from_freesound.py

import os
import sys
import random
import logging
import requests
from typing import Optional
from dotenv import load_dotenv
import freesound

# Load environment variables
load_dotenv()

# Configure logger
logger = logging.getLogger("freesound_bgm")
logging.basicConfig(level=logging.INFO)

# Freesound API setup
FREESOUND_API_KEY = os.getenv("FREESOUND_API_KEY")
OUTPUT_DIR = "assets/freesound_bgm"
os.makedirs(OUTPUT_DIR, exist_ok=True)

client = freesound.FreesoundClient()
client.set_token(FREESOUND_API_KEY, "token")


def fetch_bgm_from_freesound(category: str) -> Optional[str]:
    """
    Search and download a background music track from Freesound based on category.

    Args:
        category (str): Keyword for music search (e.g., 'motivation', 'sad').

    Returns:
        Optional[str]: Path to downloaded MP3 file or None if failed.
    """
    try:
        logger.info(f"[🔍] Searching Freesound for: {category}")
        results = client.text_search(
            query=category,
            filter="duration:[25 TO 35]",
            sort="score",
            fields="id,name,previews,duration",
            page_size=10
        )

        if results.count == 0:
            logger.warning(f"[❌] No results found for: {category}")
            return None

        sound = random.choice(results)
        filename = f"{category}_{sound.id}.mp3"
        filepath = os.path.join(OUTPUT_DIR, filename)

        if os.path.exists(filepath):
            logger.info(f"[🎵] Already downloaded: {filepath}")
            return filepath

        logger.info(f"[⬇️] Downloading: {sound.name} (ID: {sound.id})")
        preview_url = sound.previews.preview_hq_mp3
        response = requests.get(preview_url)
        response.raise_for_status()

        with open(filepath, "wb") as f:
            f.write(response.content)

        logger.info(f"[✅] Downloaded BGM to: {filepath}")
        return filepath

    except Exception as e:
        logger.exception(f"[❌] Freesound error: {e}")
        return None


# CLI test usage: python fetch_bgm_from_freesound.py motivation
if __name__ == "__main__":
    category = sys.argv[1] if len(sys.argv) > 1 else "motivation"
    path = fetch_bgm_from_freesound(category)
    print(f"🎵 Path: {path}")

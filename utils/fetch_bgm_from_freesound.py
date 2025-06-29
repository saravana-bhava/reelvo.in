# File: utils/fetch_bgm_from_freesound.py

import os
import sys
import random
import logging
import requests
import subprocess
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
if not FREESOUND_API_KEY:
    logger.error("❌ FREESOUND_API_KEY not set in .env file.")
    sys.exit(1)

OUTPUT_DIR = "assets/freesound_bgm"
os.makedirs(OUTPUT_DIR, exist_ok=True)

client = freesound.FreesoundClient()
client.set_token(FREESOUND_API_KEY, "token")


def normalize_audio(input_path: str, output_path: str) -> None:
    """
    Normalize audio using FFmpeg loudnorm filter (EBU R128 standard).
    """
    try:
        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-af", "loudnorm",
            "-ar", "44100", "-ac", "2",
            "-b:a", "192k",
            output_path
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logger.info(f"[🔊] Normalized BGM: {output_path}")
    except Exception as e:
        logger.warning(f"[⚠️] FFmpeg normalization failed: {e}")


def fetch_bgm_from_freesound(category: str) -> Optional[str]:
    """
    Search and download a background music track from Freesound based on category.
    Normalizes audio if successful.

    Args:
        category (str): Keyword for music search (e.g., 'motivation', 'sad').

    Returns:
        Optional[str]: Path to normalized MP3 file or None if failed.
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

        for sound in results:
            try:
                filename = f"{category}_{sound.id}.mp3"
                raw_path = os.path.join(OUTPUT_DIR, "raw_" + filename)
                norm_path = os.path.join(OUTPUT_DIR, filename)

                if os.path.exists(norm_path):
                    logger.info(f"[🎵] Already downloaded: {norm_path}")
                    return norm_path

                logger.info(f"[⬇️] Downloading: {sound.name} (ID: {sound.id})")
                preview_url = sound.previews.preview_hq_mp3
                response = requests.get(preview_url)
                response.raise_for_status()

                with open(raw_path, "wb") as f:
                    f.write(response.content)

                # Normalize audio
                normalize_audio(raw_path, norm_path)
                os.remove(raw_path)  # cleanup raw file

                logger.info(f"[✅] Downloaded & normalized BGM to: {norm_path}")
                return norm_path

            except Exception as e:
                logger.warning(f"[⚠️] Skipping failed download: {e}")
                continue

        logger.error("[❌] All preview downloads failed.")
        return None

    except Exception as e:
        logger.exception(f"[❌] Freesound error: {e}")
        return None


# CLI test usage: python utils/fetch_bgm_from_freesound.py motivation
if __name__ == "__main__":
    category = sys.argv[1] if len(sys.argv) > 1 else "motivation"
    path = fetch_bgm_from_freesound(category)
    print(f"🎵 Path: {path}")

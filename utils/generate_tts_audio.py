# File: utils/generate_tts_audio.py

"""
Generates TTS audio using Google Cloud TTS or gTTS (fallback).
Returns actual duration in seconds (used for dynamic 15–30s reels).
"""

import os
import subprocess
import hashlib
import logging
from typing import Tuple
from gtts import gTTS
from dotenv import load_dotenv

# Load environment
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(ROOT_DIR, ".env"))

# Logging setup
logger = logging.getLogger("tts_audio")
if not logger.hasHandlers():
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Feature flags
USE_GOOGLE_CLOUD = os.getenv("USE_GOOGLE_CLOUD_TTS", "false").lower() == "true"
DISABLE_CACHE = os.getenv("DISABLE_CACHE", "false").lower() == "true"
GOOGLE_CLOUD_TTS_VOICE = os.getenv("GOOGLE_CLOUD_TTS_VOICE", "en-US-Wavenet-D")


def get_audio_duration(path: str) -> float:
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True,
        )
        return float(result.stdout.strip())
    except Exception as e:
        logger.error(f"ffprobe failed: {e}")
        return 0.0


def generate_tts_audio(
    tts_path: str,
    language: str,
    script_text: str,
    tts_voice: str,
    cache: bool
) -> Tuple[str, float]:
    """
    Generates TTS audio and returns (output_path, duration_in_seconds).
    """
    logger.info(f"🔊 Generating TTS → {tts_path}")
    os.makedirs(os.path.dirname(tts_path), exist_ok=True)
    raw_path = tts_path.replace(".mp3", "_raw.mp3")
    success = False

    # --- Google Cloud TTS ---
    if USE_GOOGLE_CLOUD:
        try:
            from google.cloud import texttospeech
            logger.info("🧠 Using Google Cloud TTS...")

            lang_code = {"hi": "hi-IN", "en": "en-US"}.get(language, "en-US")
            voice_name = tts_voice or GOOGLE_CLOUD_TTS_VOICE

            cache_key = hashlib.md5(f"{script_text}|{language}|{voice_name}".encode("utf-8")).hexdigest()
            cache_dir = os.path.join(ROOT_DIR, "cache", "tts")
            os.makedirs(cache_dir, exist_ok=True)
            cached_path = os.path.join(cache_dir, f"{cache_key}.mp3")

            if cache and not DISABLE_CACHE and os.path.exists(cached_path):
                subprocess.run(["cp", cached_path, raw_path], check=True)
                logger.info("📦 Loaded cached Google TTS audio.")
                success = True
            else:
                client = texttospeech.TextToSpeechClient()
                synthesis_input = texttospeech.SynthesisInput(text=script_text)
                voice = texttospeech.VoiceSelectionParams(language_code=lang_code, name=voice_name)
                audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

                response = client.synthesize_speech(
                    input=synthesis_input, voice=voice, audio_config=audio_config
                )

                with open(raw_path, "wb") as f:
                    f.write(response.audio_content)

                if cache and not DISABLE_CACHE:
                    with open(cached_path, "wb") as f:
                        f.write(response.audio_content)

                logger.info("✅ Google Cloud TTS audio saved.")
                success = True
        except Exception as e:
            logger.warning(f"Google Cloud TTS failed: {e}")

    # --- gTTS Fallback ---
    if not success:
        try:
            logger.info("🌍 Using gTTS fallback...")
            lang = "hi" if language == "hi" or any('\u0900' <= c <= '\u097F' for c in script_text) else "en"
            gtts_obj = gTTS(text=script_text.strip(), lang=lang)
            gtts_obj.save(raw_path)
            logger.info("✅ gTTS audio saved.")
            success = True
        except Exception as e:
            raise RuntimeError(f"gTTS failed: {e}")

    # --- Convert to final mp3 using FFmpeg ---
    if success:
        try:
            subprocess.run([
                "ffmpeg", "-y", "-i", raw_path,
                "-ar", "44100", "-ac", "1", "-b:a", "192k",
                tts_path
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            raise RuntimeError(f"FFmpeg conversion failed: {e}")

        duration = get_audio_duration(tts_path)
        logger.info(f"🎯 TTS audio ready: {tts_path} ({duration:.1f}s)")
        return tts_path, duration

    raise RuntimeError("All TTS generation methods failed.")


# CLI usage
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 6:
        print("Usage: python utils/generate_tts_audio.py <tts_path> <language> <script_text> <tts_voice> <cache>")
        sys.exit(1)

    tts_path = sys.argv[1]
    language = sys.argv[2]
    script_text = " ".join(sys.argv[3:-2])
    tts_voice = sys.argv[-2]
    cache_str = sys.argv[-1]
    cache = cache_str.lower() in ("1", "true", "yes")

    try:
        generate_tts_audio(tts_path, language, script_text, tts_voice, cache)
    except Exception as e:
        logger.error(e)
        sys.exit(1)

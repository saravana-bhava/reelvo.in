# File: utils/gen_tts_audio.py

"""
Generates TTS audio using ElevenLabs, Google Cloud TTS, or gTTS (fallback).
Returns actual duration in seconds (used for dynamic 15–30s reels).
"""

import os
import subprocess
import hashlib
import logging
from typing import Optional, Tuple
from gtts import gTTS
from dotenv import load_dotenv

# Load environment variables
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(ROOT_DIR, ".env"))

# Logging setup
logger = logging.getLogger("tts_audio")
logging.basicConfig(level=logging.INFO)

# Feature flags
USE_ELEVENLABS = os.getenv("USE_ELEVENLABS", "false").lower() == "true"
USE_GOOGLE_CLOUD = os.getenv("USE_GOOGLE_CLOUD_TTS", "false").lower() == "true"
DISABLE_CACHE = os.getenv("DISABLE_CACHE", "false").lower() == "true"

# API keys and voice defaults
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "9BWtsMINqrJLrRacOk9x")
GOOGLE_CLOUD_TTS_VOICE = os.getenv("GOOGLE_CLOUD_TTS_VOICE", "en-US-Wavenet-D")

# Optional: progress UI
try:
    from app import progress_status
except ImportError:
    progress_status = {}

def update_progress(task_id: Optional[str], status: str, percent: int):
    if task_id and task_id in progress_status:
        progress_status[task_id] = {"status": status, "percent": percent}


def get_audio_duration(path: str) -> float:
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=True
        )
        return float(result.stdout.decode().strip())
    except Exception as e:
        logger.error(f"[❌] ffprobe failed: {e}")
        return 0.0


def generate_tts_audio(
    category: str,
    text: str,
    output_path: str,
    task_id: Optional[str] = None,
    language: str = "en",
    tts_voice: str = "en-US-Wavenet-D",
    cache: bool = True
) -> Tuple[str, float]:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    raw_path = output_path.replace(".mp3", "_raw.mp3")
    success = False

    update_progress(task_id, "🔊 Generating TTS...", 35)
    logger.info(f"[🔊] Generating TTS for '{category}' → {output_path}")

    # --- ElevenLabs ---
    if USE_ELEVENLABS and ELEVENLABS_API_KEY:
        try:
            import requests
            logger.info("[🧠] Trying ElevenLabs...")
            update_progress(task_id, "🔊 Using ElevenLabs...", 37)
            voice_id = tts_voice or ELEVENLABS_VOICE_ID
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            headers = {
                "xi-api-key": ELEVENLABS_API_KEY,
                "Content-Type": "application/json"
            }
            payload = {
                "text": text,
                "voice_settings": {"stability": 0.75, "similarity_boost": 0.75},
                "model_id": "eleven_multilingual_v2"
            }
            response = requests.post(url, headers=headers, json=payload)
            if response.ok:
                with open(raw_path, "wb") as f:
                    f.write(response.content)
                success = True
                logger.info("[✅] ElevenLabs audio saved.")
            else:
                logger.warning(f"[❌] ElevenLabs error: {response.status_code} - {response.text}")
        except Exception as e:
            logger.warning(f"[❌] ElevenLabs failed: {e}")

    # --- Google Cloud TTS ---
    if not success and USE_GOOGLE_CLOUD:
        try:
            from google.cloud import texttospeech
            logger.info("[🧠] Trying Google Cloud TTS...")
            update_progress(task_id, "🔊 Using Google Cloud TTS...", 39)

            lang_code = {"hi": "hi-IN", "en": "en-US"}.get(language, "en-US")
            voice_name = tts_voice or GOOGLE_CLOUD_TTS_VOICE
            cache_key = hashlib.md5(f"{text}|{voice_name}".encode()).hexdigest()
            cache_dir = os.path.join(ROOT_DIR, "cache", "tts")
            os.makedirs(cache_dir, exist_ok=True)
            cached_path = os.path.join(cache_dir, f"{cache_key}.mp3")

            if cache and not DISABLE_CACHE and os.path.exists(cached_path):
                subprocess.run(["cp", cached_path, raw_path], check=True)
                success = True
                logger.info("[📦] Using cached Google TTS audio.")
            else:
                client = texttospeech.TextToSpeechClient()
                synthesis_input = texttospeech.SynthesisInput(text=text)
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
                success = True
                logger.info("[✅] Google TTS audio saved.")
        except Exception as e:
            logger.warning(f"[❌] Google Cloud TTS failed: {e}")

    # --- gTTS Fallback ---
    if not success:
        try:
            update_progress(task_id, "🔊 Using gTTS fallback...", 40)
            logger.info("[🌍] Using gTTS fallback...")
            lang = "hi" if language == "hi" or any('\u0900' <= c <= '\u097F' for c in text) else "en"
            gtts_obj = gTTS(text=text.strip(), lang=lang)
            gtts_obj.save(raw_path)
            success = True
            logger.info("[✅] gTTS audio saved.")
        except Exception as e:
            raise RuntimeError(f"[❌] gTTS failed: {e}")

    # --- Final FFmpeg Conversion ---
    if success:
        try:
            subprocess.run([
                "ffmpeg", "-y", "-i", raw_path,
                "-ar", "44100", "-ac", "1", "-b:a", "192k",
                output_path
            ], check=True)
        except Exception as e:
            raise RuntimeError(f"[❌] FFmpeg conversion failed: {e}")

        duration = get_audio_duration(output_path)
        update_progress(task_id, f"✅ TTS ready ({duration:.1f}s)", 45)
        logger.info(f"[🎯] TTS audio ready: {output_path} ({duration:.1f}s)")
        return output_path, duration
    else:
        raise RuntimeError("[❌] All TTS methods failed.")


def generate_tts_from_file(
    category: str,
    username: str,
    scripts_path: str = "output/scripts",
    tts_path: str = "output/tts",
    task_id: Optional[str] = None,
    language: str = "en",
    tts_voice: str = "en-US-Wavenet-D",
    cache: bool = True
) -> Tuple[str, float]:
    text_path = os.path.join(scripts_path, username, f"{category}_text.txt")
    if not os.path.exists(text_path):
        raise FileNotFoundError(f"[❌] Script not found: {text_path}")

    with open(text_path, "r", encoding="utf-8") as f:
        text = f.read().strip()

    if not text:
        raise ValueError("[❌] Script is empty.")

    lang_suffix = f"_{language}"
    output_path = os.path.join(tts_path, username, f"{category}_voice{lang_suffix}.mp3")

    return generate_tts_audio(category, text, output_path, task_id, language, tts_voice, cache)


def generate_tts_from_text(
    text: str,
    username: str,
    output_path: str,
    category: str = "custom",
    task_id: Optional[str] = None,
    language: str = "en",
    tts_voice: str = "en-US-Wavenet-D",
    cache: bool = True
) -> Tuple[str, float]:
    return generate_tts_audio(category, text, output_path, task_id, language, tts_voice, cache)


# CLI usage
if __name__ == "__main__":
    import sys
    if len(sys.argv) == 4:
        generate_tts_from_file(sys.argv[1], sys.argv[2], language=sys.argv[3])
    elif len(sys.argv) == 3:
        generate_tts_from_file(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python utils/gen_tts_audio.py <category> <username> [language]")

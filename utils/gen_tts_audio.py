# utils/gen_tts_audio.py

"""
Generates TTS audio using ElevenLabs, Google Cloud TTS (plain text), or gTTS (fallback).
Returns actual duration in seconds (for use in dynamic 15–30s reels).
"""

import os
import subprocess
import hashlib
from gtts import gTTS
from dotenv import load_dotenv

# Load environment variables
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(ROOT_DIR, ".env"))

# Feature flags
USE_ELEVENLABS = os.getenv("USE_ELEVENLABS", "false").lower() == "true"
USE_GOOGLE_CLOUD = os.getenv("USE_GOOGLE_CLOUD_TTS", "false").lower() == "true"
DISABLE_CACHE = os.getenv("DISABLE_CACHE", "false").lower() == "true"

# API Keys & Defaults
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "9BWtsMINqrJLrRacOk9x")
GOOGLE_CLOUD_TTS_VOICE = os.getenv("GOOGLE_CLOUD_TTS_VOICE", "en-US-Wavenet-D")

# Optional UI progress
try:
    from app import progress_status
except ImportError:
    progress_status = {}

def update_progress(task_id, status, percent):
    if task_id and task_id in progress_status:
        progress_status[task_id] = {"status": status, "percent": percent}

def get_audio_duration(path: str) -> float:
    """Returns duration in seconds of the audio file."""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    return float(result.stdout.decode().strip())

def generate_tts_audio(category: str, text: str, output_path: str, task_id=None) -> tuple[str, float]:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    print(f"[🔊] Generating TTS for '{category}' → {output_path}")
    update_progress(task_id, "🔊 Generating TTS...", 35)

    raw_path = output_path.replace(".mp3", "_raw.mp3")
    success = False

    # Try ElevenLabs
    if USE_ELEVENLABS and ELEVENLABS_API_KEY:
        try:
            import requests
            print("[🧠] Trying ElevenLabs...")
            update_progress(task_id, "🔊 Using ElevenLabs...", 37)
            headers = {
                "xi-api-key": ELEVENLABS_API_KEY,
                "Content-Type": "application/json"
            }
            json_data = {
                "text": text,
                "voice_settings": {"stability": 0.75, "similarity_boost": 0.75},
                "model_id": "eleven_multilingual_v2"
            }
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
            res = requests.post(url, headers=headers, json=json_data)
            if res.status_code == 200:
                with open(raw_path, "wb") as f:
                    f.write(res.content)
                print("[✅] ElevenLabs audio saved.")
                success = True
            else:
                print(f"[❌] ElevenLabs API error: {res.status_code} - {res.text}")
        except Exception as e:
            print(f"[❌] ElevenLabs error: {e}")

    # Try Google Cloud TTS
    if not success and USE_GOOGLE_CLOUD:
        try:
            from google.cloud import texttospeech
            print("[🧠] Trying Google Cloud TTS (no SSML)...")
            update_progress(task_id, "🔊 Using Google Cloud TTS...", 39)

            lang_code = "hi-IN" if "।" in text or any('\u0900' <= c <= '\u097F' for c in text) else "en-US"
            voice_name = GOOGLE_CLOUD_TTS_VOICE

            cache_key = hashlib.md5(f"{text}|{voice_name}".encode()).hexdigest()
            cache_dir = os.path.join(ROOT_DIR, "cache", "tts")
            os.makedirs(cache_dir, exist_ok=True)
            cached_path = os.path.join(cache_dir, f"{cache_key}.mp3")

            if not DISABLE_CACHE and os.path.exists(cached_path):
                subprocess.run(["cp", cached_path, raw_path], check=True)
                print("[📦] Using cached Google TTS")
                success = True
            else:
                client = texttospeech.TextToSpeechClient()
                synthesis_input = texttospeech.SynthesisInput(text=text)
                voice = texttospeech.VoiceSelectionParams(
                    language_code=lang_code,
                    name=voice_name
                )
                audio_config = texttospeech.AudioConfig(
                    audio_encoding=texttospeech.AudioEncoding.MP3
                )
                response = client.synthesize_speech(
                    input=synthesis_input, voice=voice, audio_config=audio_config
                )
                with open(raw_path, "wb") as f:
                    f.write(response.audio_content)
                if not DISABLE_CACHE:
                    with open(cached_path, "wb") as f:
                        f.write(response.audio_content)

                print("[✅] Google Cloud TTS audio saved.")
                success = True
        except Exception as e:
            print(f"[❌] Google TTS error: {e}")

    # Fallback: gTTS
    if not success:
        try:
            print("[🌍] Using gTTS fallback...")
            update_progress(task_id, "🔊 Using gTTS fallback...", 40)
            lang = "hi" if any('\u0900' <= c <= '\u097F' for c in text) else "en"
            tts = gTTS(text=text.strip(), lang=lang)
            tts.save(raw_path)
            print("[✅] gTTS audio saved.")
            success = True
        except Exception as e:
            raise RuntimeError(f"[❌] gTTS failed: {e}")

    if success:
        subprocess.run([
            "ffmpeg", "-y", "-i", raw_path,
            "-ar", "44100", "-ac", "1", "-b:a", "192k",
            output_path
        ], check=True)
        duration = get_audio_duration(output_path)
        update_progress(task_id, f"✅ TTS ready ({duration:.1f}s)", 45)
        print(f"[🎯] Final audio saved: {output_path} ({duration:.1f}s)")
        return output_path, duration
    else:
        raise RuntimeError("[❌] All TTS methods failed.")

def generate_tts_from_file(category: str, username: str, output_root: str = "output", task_id=None) -> tuple[str, float]:
    text_path = os.path.join(output_root, username, f"{category}_text.txt")
    if not os.path.exists(text_path):
        raise FileNotFoundError(f"[❌] Script not found: {text_path}")
    with open(text_path, "r", encoding="utf-8") as f:
        text = f.read().strip()
    if not text:
        raise ValueError("[❌] Script text is empty.")
    output_path = os.path.join(output_root, username, f"{category}.mp3")
    return generate_tts_audio(category, text, output_path, task_id)


# CLI usage
if __name__ == "__main__":
    import sys
    if len(sys.argv) == 3:
        generate_tts_from_file(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python utils/gen_tts_audio.py <category> <username>")

# utils/gen_tts_audio.py

"""
Generates TTS audio using ElevenLabs, Google Cloud TTS (with <mark> metadata), or gTTS (fallback).
Pads all audio to exactly 30s for Instagram Reels.
"""

import os
import subprocess
import hashlib
import json
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

def pad_or_trim_audio(input_path: str, output_path: str, duration: int = 30):
    try:
        subprocess.run([
            "ffmpeg", "-y", "-i", input_path,
            "-af", f"adelay=500|500,apad=pad_dur={duration}",
            "-t", str(duration),
            "-ar", "44100", "-ac", "1", "-b:a", "192k",
            output_path
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"[❌] FFmpeg padding failed: {e}")

def make_ssml_with_marks(text: str) -> tuple[str, list[str]]:
    """
    Convert plain text into SSML format with <mark> tags between sentences.
    """
    import re
    sentences = re.split(r'(?<=[.?!])\s+', text.strip())
    ssml_lines = ['<speak>']
    marks = []

    for i, sentence in enumerate(sentences):
        sentence = sentence.strip()
        if not sentence:
            continue
        mark_name = f"mark{i+1}"
        marks.append(mark_name)
        ssml_lines.append(f'<mark name="{mark_name}"/>{sentence}')

    ssml_lines.append('</speak>')
    return "\n".join(ssml_lines), marks

def generate_tts_audio(category: str, text: str, output_path: str, task_id=None) -> str:
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

    # Try Google Cloud TTS with <mark> metadata
    if not success and USE_GOOGLE_CLOUD:
        try:
            from google.cloud import texttospeech
            print("[🧠] Trying Google Cloud TTS...")
            update_progress(task_id, "🔊 Using Google Cloud TTS...", 39)

            ssml_text, mark_names = make_ssml_with_marks(text)
            cache_key = hashlib.md5(f"{ssml_text}|{GOOGLE_CLOUD_TTS_VOICE}".encode()).hexdigest()
            cache_dir = os.path.join(ROOT_DIR, "cache", "tts")
            os.makedirs(cache_dir, exist_ok=True)
            cached_path = os.path.join(cache_dir, f"{cache_key}.mp3")
            marks_path = output_path.replace(".mp3", ".marks.json")

            if not DISABLE_CACHE and os.path.exists(cached_path):
                subprocess.run(["cp", cached_path, raw_path], check=True)
                print("[📦] Using cached Google TTS")
                success = True
            else:
                client = texttospeech.TextToSpeechClient()
                synthesis_input = texttospeech.SynthesisInput(ssml=ssml_text)
                voice = texttospeech.VoiceSelectionParams(
                    language_code="hi-IN" if "।" in text or any('\u0900' <= c <= '\u097F' for c in text) else "en-US",
                    name=GOOGLE_CLOUD_TTS_VOICE
                )
                audio_config = texttospeech.AudioConfig(
                    audio_encoding=texttospeech.AudioEncoding.MP3,
                    enable_time_pointing=[texttospeech.SynthesizeSpeechRequest.TimepointType.SSML_MARK]
                )
                response = client.synthesize_speech(
                    input=synthesis_input, voice=voice, audio_config=audio_config
                )

                # Save audio
                with open(raw_path, "wb") as f:
                    f.write(response.audio_content)
                if not DISABLE_CACHE:
                    with open(cached_path, "wb") as f:
                        f.write(response.audio_content)

                # Save mark timing metadata
                marks_data = [
                    {"mark": tp.mark_name, "time": round(tp.time_seconds, 3)}
                    for tp in response.timepoints
                ]
                with open(marks_path, "w", encoding="utf-8") as f:
                    json.dump(marks_data, f, ensure_ascii=False, indent=2)
                print(f"[✅] Google TTS audio & marks saved → {marks_path}")
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

    # Final padding
    if success:
        update_progress(task_id, "🎧 Padding audio...", 42)
        pad_or_trim_audio(raw_path, output_path)
        update_progress(task_id, "✅ TTS audio ready", 45)
        print(f"[🎯] Final audio saved: {output_path}")
        return output_path
    else:
        raise RuntimeError("[❌] All TTS methods failed.")

def generate_tts_from_file(category: str, username: str, output_root: str = "output", task_id=None) -> str:
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

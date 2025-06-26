# utils/gen_tts_audio.py

import os
import subprocess
from gtts import gTTS
from dotenv import load_dotenv

# Load .env from project root
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(ROOT_DIR, ".env"))

USE_ELEVENLABS = os.getenv("USE_ELEVENLABS", "false").lower() == "true"
USE_GOOGLE_CLOUD = os.getenv("USE_GOOGLE_CLOUD_TTS", "false").lower() == "true"

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "9BWtsMINqrJLrRacOk9x")
GOOGLE_CLOUD_TTS_VOICE = os.getenv("GOOGLE_CLOUD_TTS_VOICE", "en-US-Wavenet-D")


def pad_or_trim_audio(input_path, output_path, duration=10):
    try:
        subprocess.run([
            "ffmpeg", "-y", "-i", input_path,
            "-af", f"apad=pad_dur={duration}",
            "-t", str(duration),
            "-ar", "44100", "-ac", "1", "-b:a", "192k",
            output_path
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"[❌] FFmpeg padding failed: {e}")


def generate_tts_audio(category: str, text: str, output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    print(f"[🔊] Generating TTS for '{category}' → {output_path}")

    raw_path = output_path.replace(".mp3", "_raw.mp3")
    success = False

    # Attempt: ElevenLabs
    if USE_ELEVENLABS and ELEVENLABS_API_KEY:
        try:
            import requests
            print("[🧠] Trying ElevenLabs TTS...")
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
            response = requests.post(url, headers=headers, json=json_data)

            if response.status_code == 200:
                with open(raw_path, "wb") as f:
                    f.write(response.content)
                print(f"[✅] ElevenLabs audio saved → {raw_path}")
                success = True
            else:
                print(f"[❌] ElevenLabs API error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"[❌] ElevenLabs TTS failed: {e}")

    # Attempt: Google Cloud TTS
    if not success and USE_GOOGLE_CLOUD:
        try:
            print("[🧠] Trying Google Cloud TTS...")
            from google.cloud import texttospeech
            client = texttospeech.TextToSpeechClient()

            synthesis_input = texttospeech.SynthesisInput(text=text)
            voice = texttospeech.VoiceSelectionParams(
                language_code="en-IN",  # or en-US
                name=GOOGLE_CLOUD_TTS_VOICE
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )

            response = client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=audio_config
            )

            with open(raw_path, "wb") as out:
                out.write(response.audio_content)
            print(f"[✅] Google Cloud TTS audio saved → {raw_path}")
            success = True
        except Exception as e:
            print(f"[❌] Google Cloud TTS failed: {e}")

    # Fallback: gTTS
    if not success:
        try:
            print("[🌍] Falling back to gTTS...")
            tts = gTTS(text=text.strip(), lang='en')
            tts.save(raw_path)
            print(f"[✅] gTTS audio saved → {raw_path}")
            success = True
        except Exception as e:
            raise RuntimeError(f"[❌] gTTS failed: {e}")

    # Finalize
    if success:
        pad_or_trim_audio(raw_path, output_path)
        print(f"[🎯] Audio padded to 10s → {output_path}")
        return output_path
    else:
        raise RuntimeError("[❌] All TTS methods failed.")


def generate_tts_from_file(category: str, username: str, output_root: str = "output"):
    output_dir = os.path.join(output_root, username)
    text_path = os.path.join(output_dir, f"{category}_text.txt")

    if not os.path.exists(text_path):
        raise FileNotFoundError(f"[❌] Text file not found: {text_path}")

    with open(text_path, "r", encoding="utf-8") as f:
        text = f.read().strip()

    if not text:
        raise ValueError("[❌] Script text is empty.")

    output_path = os.path.join(output_dir, f"{category}.mp3")
    return generate_tts_audio(category, text, output_path)


# CLI entry
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python utils/gen_tts_audio.py <category> <username>")
    else:
        generate_tts_from_file(sys.argv[1], sys.argv[2])

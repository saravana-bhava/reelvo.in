# test/elevenlabs_test.py

import os
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs import play

# Load environment variables from .env in the project root
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.env"))
load_dotenv(dotenv_path=dotenv_path)

API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb")
TEXT = "The first move is what sets everything in motion."

if not API_KEY:
    raise EnvironmentError("[❌] ELEVENLABS_API_KEY not found in .env")

try:
    client = ElevenLabs(api_key=API_KEY)
    audio = client.text_to_speech.convert(
        text=TEXT,
        voice_id=VOICE_ID,
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    )

    print("[✅] TTS audio retrieved successfully. Playing now...")
    play(audio)

except Exception as e:
    print(f"[❌] Error with ElevenLabs API: {e}")

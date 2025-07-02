# test/google_text-to-speech_test.py

import os
from dotenv import load_dotenv
from google.cloud import texttospeech

# Load .env from root
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(dotenv_path=os.path.join(ROOT_DIR, ".env"))

GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

if not GOOGLE_CREDENTIALS_PATH or not os.path.exists(GOOGLE_CREDENTIALS_PATH):
    raise EnvironmentError("[❌] GOOGLE_APPLICATION_CREDENTIALS path is missing or invalid in .env")

# Set the required environment variable for Google SDK
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_CREDENTIALS_PATH

try:
    client = texttospeech.TextToSpeechClient()

    synthesis_input = texttospeech.SynthesisInput(text="Hello from Google Cloud TTS")

    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name="en-US-Wavenet-D",  # You can customize this in your .env if needed
        ssml_gender=texttospeech.SsmlVoiceGender.MALE
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    output_file = os.path.join(ROOT_DIR, "output", "google_tts_test.mp3")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "wb") as out:
        out.write(response.audio_content)

    print(f"[✅] Audio content written to: {output_file}")

except Exception as e:
    print(f"[❌] Google Cloud TTS failed: {e}")

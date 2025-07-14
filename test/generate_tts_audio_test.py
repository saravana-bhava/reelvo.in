# File: test/generate_tts_audio_test.py

import sys
import os
import pytest

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.generate_tts_audio import generate_tts_audio

TEST_EMAIL = "developer@sazm.in"
OUTPUT_ROOT = "output"
SCRIPTS_DIR = os.path.join(OUTPUT_ROOT, TEST_EMAIL, "scripts")
TTS_DIR = os.path.join(OUTPUT_ROOT, TEST_EMAIL, "tts")

def generate_tts_from_text(text, user_email, output_path, theme, task_id, language, tts_voice, cache):
    return generate_tts_audio(output_path, language, text, tts_voice, cache)

def generate_tts_from_file(theme, user_email, output_root, task_id, language, tts_voice, cache):
    script_path = os.path.join(output_root, user_email, "scripts", "demo_text.txt")
    if not os.path.exists(script_path):
        raise FileNotFoundError(f"Script file not found: {script_path}")
    with open(script_path, "r", encoding="utf-8") as f:
        text = f.read()
    tts_path = os.path.join(output_root, user_email, "tts", "demo_voice_en.mp3")
    return generate_tts_audio(tts_path, language, text, tts_voice, cache)

@pytest.fixture
def setup_output_file():
    os.makedirs(TTS_DIR, exist_ok=True)
    path = os.path.join(TTS_DIR, "test_output.mp3")
    if os.path.exists(path):
        os.remove(path)
    yield path
    if os.path.exists(path):
        os.remove(path)

@pytest.fixture
def setup_input_script():
    os.makedirs(SCRIPTS_DIR, exist_ok=True)
    path = os.path.join(SCRIPTS_DIR, "demo_text.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("This is a test script for file-based TTS.")
    yield path
    if os.path.exists(path):
        os.remove(path)

@pytest.fixture
def cleanup_voice_file():
    voice_path = os.path.join(TTS_DIR, "demo_voice_en.mp3")
    if os.path.exists(voice_path):
        os.remove(voice_path)
    yield voice_path
    if os.path.exists(voice_path):
        os.remove(voice_path)

def test_generate_tts_audio_from_text(setup_output_file):
    text = "Testing TTS generation directly from text input."
    out_path = setup_output_file
    path, duration = generate_tts_from_text(
        text=text,
        user_email=TEST_EMAIL,
        output_path=out_path,
        theme="motivation",
        task_id=None,
        language="en",
        tts_voice="en-US-Wavenet-D",
        cache=False
    )
    assert os.path.exists(path)
    assert duration > 0
    print(f"✅ Text-based TTS audio generated at {path} ({duration:.2f}s)")

def test_generate_tts_audio_hindi(setup_output_file):
    text = "यह एक परीक्षण है जो हिंदी में है।"
    out_path = setup_output_file
    path, duration = generate_tts_from_text(
        text=text,
        user_email=TEST_EMAIL,
        output_path=out_path,
        theme="motivation",
        task_id=None,
        language="hi",
        tts_voice="hi-IN-Wavenet-A",
        cache=False
    )
    assert os.path.exists(path)
    assert duration > 0
    print(f"✅ Hindi TTS audio generated at {path} ({duration:.2f}s)")

def test_generate_tts_audio_from_file(setup_input_script, cleanup_voice_file):
    path, duration = generate_tts_from_file(
        theme="motivation",
        user_email=TEST_EMAIL,
        output_root=OUTPUT_ROOT,
        task_id=None,
        language="en",
        tts_voice="en-US-Wavenet-D",
        cache=False
    )
    assert os.path.exists(path)
    assert duration > 0
    print(f"✅ File-based TTS audio generated at {path} ({duration:.2f}s)")

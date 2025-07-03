# File: test/generate_tts_audio_test.py

import sys
import os
import pytest

# Add project root to sys.path to import main.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.generate_tts_audio import generate_tts_from_text, generate_tts_from_file

TEST_USERNAME = "test"
OUTPUT_ROOT = "output"
SCRIPTS_DIR = os.path.join(OUTPUT_ROOT, TEST_USERNAME, "scripts")
TTS_DIR = os.path.join(OUTPUT_ROOT, TEST_USERNAME, "tts")

@pytest.fixture
def setup_output_file():
    os.makedirs(TTS_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_ROOT, TEST_USERNAME, "tts", "test_output.mp3")
    if os.path.exists(path):
        os.remove(path)
    yield path
    if os.path.exists(path):
        os.remove(path)

@pytest.fixture
def setup_input_script():
    os.makedirs(SCRIPTS_DIR, exist_ok=True)
    text_path = os.path.join(OUTPUT_ROOT, TEST_USERNAME, "scripts", "demo_text.txt")
    with open(text_path, "w", encoding="utf-8") as f:
        f.write("This is a test script for file-based TTS.")
    yield text_path
    if os.path.exists(text_path):
        os.remove(text_path)

@pytest.fixture
def cleanup_voice_file():
    voice_path = os.path.join(OUTPUT_ROOT, TEST_USERNAME, "tts", "demo_voice_en.mp3")
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
        user_name=TEST_USERNAME,
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
        user_name=TEST_USERNAME,
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
        user_name=TEST_USERNAME,
        output_root=OUTPUT_ROOT,
        task_id=None,
        language="en",
        tts_voice="en-US-Wavenet-D",
        cache=False
    )
    assert os.path.exists(path)
    assert duration > 0
    print(f"✅ File-based TTS audio generated at {path} ({duration:.2f}s)")

# run_pipeline.py

import sys
import os
from utils.generate_script import save_script
from utils.gen_tts_audio import generate_tts_from_file
from utils.gen_subtitles import generate_srt_from_file
from utils.gen_text_overlay import generate_text_overlay
from create_video import create_video_for_category

def run_pipeline(category: str):
    print(f"\n⚙️ Starting pipeline for: {category.upper()}")

    # 1. Generate script and save to output/{category}_text.txt
    try:
        script_path = save_script(category)
    except Exception as e:
        print(f"[❌] Script generation failed: {e}")
        return

    # 2. Read script from file
    try:
        with open(script_path, "r", encoding="utf-8") as f:
            script = f.read().strip()
    except Exception as e:
        print(f"[❌] Failed to read script text: {e}")
        return

    # 3. Generate TTS audio
    try:
        generate_tts_from_file(category)
    except Exception as e:
        print(f"[❌] TTS generation failed: {e}")
        return

    # 4. Generate subtitles
    try:
        generate_srt_from_file(category)
    except Exception as e:
        print(f"[❌] Subtitle generation failed: {e}")
        return

    # 5. Generate text overlay image
    try:
        text_image_path = f"output/{category}_text.png"
        generate_text_overlay(script, text_image_path)
    except Exception as e:
        print(f"[❌] Text overlay image failed: {e}")
        return

    # 6. Final video creation
    try:
        create_video_for_category(category)
    except Exception as e:
        print(f"[❌] Video creation failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python run_pipeline.py <category>")
        print("Example: python run_pipeline.py motivation")
    else:
        run_pipeline(sys.argv[1].lower())

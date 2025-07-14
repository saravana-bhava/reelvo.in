# File: test/fetch_bgm_test.py

import sys
import os

# Add the project root to sys.path so "utils" is found
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.fetch_bgm import fetch_bgm
from utils.generate_script import generate_script_for_user
from utils.translate_text import translate_to_english

def main():
    print("[🧪] Starting BGM fetch test...")

    # Step 1: Generate a script in Hindi
    try:
        text_path = generate_script_for_user("posturefix", "demo", "hi")
        with open(text_path, "r", encoding="utf-8") as f:
            script = f.read().strip()
        print("\n[📝] Original Script (Hindi):\n", script)
    except Exception as e:
        print(f"[❌] Failed to generate script: {e}")
        return

    # Step 2: Translate to English
    try:
        english_script = translate_to_english(script)
        print("\n[🌐] Translated Script (English):\n", english_script)
    except Exception as e:
        print(f"[❌] Failed to translate script: {e}")
        return

    # Step 3: Fetch BGM
    try:
        bgm_path = fetch_bgm(english_script, "en", "default")
        if bgm_path:
            print(f"\n[✅] BGM fetched or fallback used: {bgm_path}")
        else:
            print(f"\n[⚠️] No BGM found. Using silence or skipping.")
    except Exception as e:
        print(f"\n[❌] Failed to fetch BGM: {e}")

if __name__ == "__main__":
    main()

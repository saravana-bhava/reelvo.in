# File: test/fetch_bgm_test.py

import sys
import os

# Add the project root to sys.path so "utils" is found
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.fetch_bgm import fetch_bgm
from utils.generate_script import generate_script_for_user
from utils.translate_text import translate_to_english

if __name__ == "__main__":
    text_path = generate_script_for_user("posturefix", "demo", "hi")
    with open(text_path, "r", encoding="utf-8") as f:
        script = f.read().strip()
    print(script)

    english_script = translate_to_english(script)
    print(english_script)

    try:
        bgm_path = fetch_bgm(english_script, "en", "default")
        if bgm_path:
            print(f"[✅] BGM fetched or fallback used: {bgm_path}")
        else:
            print(f"[⚠️] No BGM found. Using silence or skipping.")
    except Exception as e:
        print(f"[❌] Failed to fetch BGM: {e}")

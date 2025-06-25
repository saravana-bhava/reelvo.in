# utils/gen_tts_audio.py

import os
from gtts import gTTS

def generate_tts_audio(category: str, text: str, output_path: str = None):
    output_path = output_path or f"output/{category}.mp3"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print(f"[🔊] Generating TTS for '{category}' → {output_path}")
    tts = gTTS(text=text.strip(), lang='en')
    tts.save(output_path)
    print(f"[✅] TTS saved to {output_path}")
    return output_path

def generate_tts_from_file(category: str, output_dir: str = "output"):
    text_path = os.path.join(output_dir, f"{category}_text.txt")
    if not os.path.exists(text_path):
        raise FileNotFoundError(f"[❌] Text file not found: {text_path}")

    with open(text_path, "r", encoding="utf-8") as f:
        text = f.read().strip()

    if not text:
        raise ValueError("[❌] Script text is empty.")

    output_path = os.path.join(output_dir, f"{category}.mp3")
    return generate_tts_audio(category, text, output_path)

# CLI usage
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python utils/gen_tts_audio.py <category>")
    else:
        generate_tts_from_file(sys.argv[1])

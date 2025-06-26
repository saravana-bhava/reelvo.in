# utils/gen_subtitles.py

import os
import whisper
import srt
import re
import warnings
from datetime import timedelta

# Suppress Whisper's FP16 warning on CPU
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")

# Load Whisper model once
MODEL = whisper.load_model("large")

def split_into_sentences(text):
    return re.split(r'(?<=[.!?])\s+', text.strip())

def generate_srt_from_audio(category: str, audio_path: str, output_path: str):
    print(f"[🧠] Transcribing audio for word-aligned subtitles: {audio_path}")

    try:
        result = MODEL.transcribe(audio_path, word_timestamps=True)
    except Exception as e:
        raise RuntimeError(f"[❌] Whisper transcription failed: {e}")

    words = []
    for segment in result.get("segments", []):
        words.extend(segment.get("words", []))

    if not words:
        raise ValueError("[❌] No words found in transcription.")

    full_text = result.get("text", "")
    sentences = split_into_sentences(full_text)

    subtitles = []
    index = 1
    word_idx = 0

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        sentence_words = sentence.split()
        match_len = len(sentence_words)
        matched_words = []

        # Try exact match
        while word_idx + match_len <= len(words):
            chunk = words[word_idx:word_idx + match_len]
            chunk_text = " ".join(w["word"].strip() for w in chunk)
            if chunk_text.replace("’", "'") == sentence.replace("’", "'"):
                matched_words = chunk
                break
            word_idx += 1

        # If exact match fails, fallback to approximate match
        if not matched_words:
            for i in range(len(words) - match_len):
                chunk = words[i:i + match_len]
                chunk_text = " ".join(w["word"].strip().lower() for w in chunk)
                if sentence.lower() in chunk_text:
                    matched_words = chunk
                    break

        if not matched_words:
            print(f"[⚠️] Could not align sentence: '{sentence}'")
            continue

        start = matched_words[0]["start"]
        end = matched_words[-1]["end"] + (0.4 if sentence.endswith((".", "!", "?")) else 0)

        subtitles.append(srt.Subtitle(
            index=index,
            start=timedelta(seconds=start),
            end=timedelta(seconds=end),
            content=sentence
        ))
        index += 1
        word_idx += match_len

    # Save subtitles
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(srt.compose(subtitles))

    print(f"[✅] Generated SRT for '{category}' → {output_path}")

# CLI usage
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python utils/gen_subtitles.py <category> <audio_path>")
    else:
        category = sys.argv[1]
        audio_file = sys.argv[2]
        output_srt = os.path.splitext(audio_file)[0] + ".srt"
        generate_srt_from_audio(category, audio_file, output_srt)

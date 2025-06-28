# utils/gen_subtitles.py

import os
import whisper
import srt
import warnings
from datetime import timedelta

warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")
MODEL = whisper.load_model("small")

def generate_srt_from_audio(category: str, audio_path: str, output_path: str, words_per_line=6):
    print(f"[🧠] Transcribing audio for subtitles (Whisper): {audio_path}")

    try:
        result = MODEL.transcribe(audio_path, word_timestamps=True)
    except Exception as e:
        raise RuntimeError(f"[❌] Whisper transcription failed: {e}")

    words = []
    for segment in result.get("segments", []):
        words.extend(segment.get("words", []))

    if not words:
        raise ValueError("[❌] No words found in transcription.")

    subtitles = []
    index = 1

    for i in range(0, len(words), words_per_line):
        chunk = words[i:i + words_per_line]
        if not chunk:
            continue

        text = " ".join(w["word"].strip() for w in chunk)
        start = chunk[0]["start"]
        end = chunk[-1]["end"]

        # Add a tiny buffer
        end += 0.2 if not text.endswith(".") else 0.4

        subtitles.append(srt.Subtitle(
            index=index,
            start=timedelta(seconds=start),
            end=timedelta(seconds=end),
            content=text
        ))
        index += 1

    # Fill remaining time if silence at the end
    last_end = subtitles[-1].end.total_seconds()
    if last_end < 29.0:
        subtitles.append(srt.Subtitle(
            index=index,
            start=timedelta(seconds=last_end + 0.2),
            end=timedelta(seconds=29.5),
            content="..."
        ))
        print(f"[➕] Appended trailing subtitle (...) from {last_end + 0.2:.2f}s to 29.5s")

    # Save SRT
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

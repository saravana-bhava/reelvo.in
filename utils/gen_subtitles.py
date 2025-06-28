# utils/gen_subtitles.py

"""
Subtitle generator using OpenAI Whisper for audio-based transcription.

If Google Cloud TTS SSML <mark> data is unavailable, this script
generates a fallback .srt subtitle file from raw audio.
"""

import os
import srt
import whisper
import warnings
from datetime import timedelta

# Silence known warning
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")

# Load Whisper model once
MODEL = whisper.load_model("small")

# Optional progress bar integration
try:
    from progress import update_progress
except ImportError:
    def update_progress(task_id, status, percent):
        pass


def generate_srt_from_audio(category: str, audio_path: str, output_path: str, words_per_line: int = 6, task_id: str | None = None):
    """
    Generate SRT subtitle file using Whisper from a given audio clip.

    Args:
        category (str): Category name (used in logs).
        audio_path (str): Path to the .mp3/.wav file.
        output_path (str): Target path for .srt file.
        words_per_line (int): How many words per subtitle line.
        task_id (str | None): Task ID for UI progress updates.
    """
    update_progress(task_id, "📝 Generating subtitles...", 50)
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
    min_duration = 1.5
    max_duration = 4.0
    min_gap = 0.1
    last_end_time = 0.5  # Start offset for fade-in sync

    i = 0
    while i < len(words):
        chunk = words[i:i + words_per_line]
        if not chunk:
            break

        text = " ".join(w["word"].strip() for w in chunk)
        start = max(chunk[0]["start"], last_end_time + min_gap)
        end = chunk[-1]["end"]

        # Clamp duration
        duration = end - start
        if duration < min_duration:
            end = start + min_duration
        elif duration > max_duration:
            end = start + max_duration

        end = min(end, 29.5)

        subtitles.append(srt.Subtitle(
            index=index,
            start=timedelta(seconds=start),
            end=timedelta(seconds=end),
            content=text
        ))

        last_end_time = end
        index += 1
        i += words_per_line

    # Add trailing subtitle if time remaining
    if subtitles and subtitles[-1].end.total_seconds() < 29.5:
        subtitles.append(srt.Subtitle(
            index=index,
            start=timedelta(seconds=subtitles[-1].end.total_seconds() + 0.2),
            end=timedelta(seconds=29.5),
            content="..."
        ))
        print(f"[➕] Appended trailing subtitle (...) from {subtitles[-1].start.total_seconds():.2f}s to 29.5s")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(srt.compose(subtitles))

    print(f"[✅] Generated SRT for '{category}' → {output_path}")
    update_progress(task_id, "✅ Subtitles ready", 55)


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

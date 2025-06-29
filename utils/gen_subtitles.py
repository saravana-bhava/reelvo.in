# utils/gen_subtitles.py

"""
Subtitle generator using Google TTS <mark> metadata or Whisper fallback.

Priority:
1. Use .marks.json generated from Google Cloud TTS SSML for accurate word timing.
2. If unavailable, use OpenAI Whisper model for transcription.

Generates: .srt subtitle file for overlay on final Instagram Reels.
Optionally converts .srt → .ass for rendering Hindi or non-Latin fonts correctly.
"""

import os
import json
import srt
import whisper
import warnings
from datetime import timedelta

# Suppress Whisper FP16 warning
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")

# Load Whisper model once
MODEL = whisper.load_model("small")

# Optional progress bar hook
try:
    from progress import update_progress
except ImportError:
    def update_progress(task_id, status, percent): pass


def generate_srt_from_marks_json(json_path: str, output_path: str, words_per_line: int = 6):
    """
    Generate .srt file from Google TTS SSML <mark> .json timings.

    Format: [
        { "start": 0.3, "word": "आपका" },
        { "start": 0.6, "word": "सपना" },
        ...
    ]
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    subtitles = []
    index = 1
    last_end = 0.5
    min_duration = 1.5
    max_duration = 4.0
    min_gap = 0.1

    i = 0
    while i < len(data):
        chunk = data[i:i + words_per_line]
        text = " ".join([w["word"].strip() for w in chunk])
        start = max(chunk[0]["start"], last_end + min_gap)
        end = chunk[-1]["start"] + 0.4  # assume ~0.4s word avg

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
        last_end = end
        index += 1
        i += words_per_line

    if subtitles and subtitles[-1].end.total_seconds() < 29.5:
        subtitles.append(srt.Subtitle(
            index=index,
            start=timedelta(seconds=subtitles[-1].end.total_seconds() + 0.2),
            end=timedelta(seconds=29.5),
            content="..."
        ))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(srt.compose(subtitles))

    print(f"[✅] Subtitles from <mark> JSON → {output_path}")


def generate_srt_from_audio(category: str, audio_path: str, output_path: str, words_per_line: int = 6, task_id: str | None = None):
    """
    Generate .srt subtitles from .marks.json or Whisper.

    Args:
        category (str): For logging.
        audio_path (str): Path to audio (.mp3/.wav).
        output_path (str): Where to save .srt file.
    """
    update_progress(task_id, "📝 Generating subtitles...", 50)
    print(f"[🔍] Looking for marks.json near: {audio_path}")

    base_path = os.path.splitext(audio_path)[0]
    marks_path = base_path + ".marks.json"

    # --- Preferred: Use Google TTS mark timings ---
    if os.path.exists(marks_path):
        print(f"[✅] Found SSML <mark> metadata → {marks_path}")
        generate_srt_from_marks_json(marks_path, output_path, words_per_line)
        update_progress(task_id, "✅ Subtitles ready (from Google TTS)", 55)
        return

    # --- Fallback: Whisper-based ---
    print(f"[❗] marks.json not found → falling back to Whisper: {audio_path}")
    print(f"[🧠] Transcribing audio for subtitles (Whisper)...")

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
    last_end_time = 0.5

    i = 0
    while i < len(words):
        chunk = words[i:i + words_per_line]
        if not chunk:
            break

        text = " ".join(w["word"].strip() for w in chunk)
        start = max(chunk[0]["start"], last_end_time + min_gap)
        end = chunk[-1]["end"]

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

    if subtitles and subtitles[-1].end.total_seconds() < 29.5:
        subtitles.append(srt.Subtitle(
            index=index,
            start=timedelta(seconds=subtitles[-1].end.total_seconds() + 0.2),
            end=timedelta(seconds=29.5),
            content="..."
        ))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(srt.compose(subtitles))

    print(f"[✅] Generated Whisper SRT for '{category}' → {output_path}")
    update_progress(task_id, "✅ Subtitles ready (Whisper)", 55)


def convert_srt_to_ass(srt_path: str, ass_path: str, font: str = "Noto Sans Devanagari", fontsize: int = 18):
    """
    Convert SRT subtitles to ASS format for better font rendering (e.g. Hindi).

    Args:
        srt_path (str): Input .srt subtitle path.
        ass_path (str): Output .ass subtitle path.
        font (str): Font name for subtitle rendering.
        fontsize (int): Font size for rendering.
    """
    with open(srt_path, "r", encoding="utf-8") as f:
        subs = list(srt.parse(f.read()))

    def format_time(t: timedelta):
        total = int(t.total_seconds())
        hours = total // 3600
        minutes = (total % 3600) // 60
        seconds = total % 60
        cs = int((t.total_seconds() - total) * 100)
        return f"{hours}:{minutes:02}:{seconds:02}.{cs:02}"

    ass_header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font},{fontsize},&H00FFFFFF,&H80000000,1,2,0,2,10,10,100,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    ass_events = ""
    for sub in subs:
        start = format_time(sub.start)
        end = format_time(sub.end)
        text = sub.content.replace("\n", " ").strip()
        ass_events += f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}\n"

    os.makedirs(os.path.dirname(ass_path), exist_ok=True)
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_header + ass_events)

    print(f"[🈶] Converted SRT → ASS → {ass_path}")


# CLI
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python utils/gen_subtitles.py <category> <audio_path>")
    else:
        category = sys.argv[1]
        audio_file = sys.argv[2]
        output_srt = os.path.splitext(audio_file)[0] + ".srt"
        generate_srt_from_audio(category, audio_file, output_srt)
        # Optional: convert_srt_to_ass(output_srt, output_srt.replace(".srt", ".ass"))

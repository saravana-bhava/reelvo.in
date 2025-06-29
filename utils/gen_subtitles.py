# utils/gen_subtitles.py

"""
Subtitle generator using Whisper fallback.

Priority:
1. use OpenAI Whisper model for transcription.

Generates:
- .srt subtitle file for overlay on final Instagram Reels.
- Automatically converts .srt → .ass for rendering Hindi (Devanagari) correctly.
"""

import os
import json
import srt
import whisper
import warnings
from datetime import timedelta

warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")

MODEL = whisper.load_model("small")

try:
    from progress import update_progress
except ImportError:
    def update_progress(task_id, status, percent): pass


def generate_srt_from_audio(category: str, audio_path: str, output_path: str, words_per_line: int = 6, task_id: str | None = None):
    update_progress(task_id, "📝 Generating subtitles...", 50)
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

    # Auto-convert to ASS if Hindi detected
    all_text = " ".join(sub.content for sub in subtitles)
    if any('\u0900' <= c <= '\u097F' for c in all_text):
        ass_path = output_path.replace(".srt", ".ass")
        convert_srt_to_ass(output_path, ass_path, font="Noto Sans Devanagari")
        print(f"[🈶] Detected Hindi — ASS subtitle created: {ass_path}")


def convert_srt_to_ass(srt_path: str, ass_path: str, font: str = "Noto Sans Devanagari", fontsize: int = 18):
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

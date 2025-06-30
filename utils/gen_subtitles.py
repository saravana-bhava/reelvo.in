# File: utils/gen_subtitles.py

"""
Subtitle generator using Whisper fallback.

Priority:
1. Use OpenAI Whisper model for transcription if Google TTS marks are unavailable.

Generates:
- .srt subtitle file for overlay on Instagram Reels.
- Automatically converts .srt → .ass for proper Hindi (Devanagari) subtitle rendering.
"""

import os
import srt
import whisper
import warnings
import logging
from datetime import timedelta
from typing import Optional

# Logging setup
logger = logging.getLogger("subtitle_gen")
logging.basicConfig(level=logging.INFO)

# Suppress FP16 warning
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")

# Load Whisper model
try:
    MODEL = whisper.load_model("small")
except Exception as e:
    logger.error(f"[❌] Failed to load Whisper model: {e}")
    raise

# Optional real-time progress updater
try:
    from progress import update_progress
except ImportError:
    def update_progress(task_id: str, status: str, percent: int): pass


def generate_srt_from_audio(
    category: str,
    audio_path: str,
    output_path: str,
    words_per_line: int = 6,
    task_id: Optional[str] = None,
    language: str = "auto"
) -> None:
    """
    Generate SRT subtitles using OpenAI Whisper.

    Args:
        category (str): Video category (e.g., 'motivation').
        audio_path (str): Path to the audio file (mp3).
        output_path (str): Where to save the .srt file.
        words_per_line (int): Number of words per subtitle line.
        task_id (Optional[str]): Optional task ID for progress updates.
        language (str): Language code ('en', 'hi', or 'auto').
    """
    update_progress(task_id, "📝 Generating subtitles...", 50)
    logger.info(f"[🧠] Transcribing audio for subtitles with Whisper...")

    # Auto-detect Hindi if needed
    if language == "auto":
        language = "en"
        try:
            txt_path = audio_path.replace(".mp3", ".txt")
            if os.path.exists(txt_path):
                with open(txt_path, "r", encoding="utf-8") as f:
                    raw_text = f.read()
                    if any('\u0900' <= c <= '\u097F' for c in raw_text):
                        language = "hi"
        except Exception:
            pass

    try:
        result = MODEL.transcribe(audio_path, word_timestamps=True, language=language)
    except Exception as e:
        raise RuntimeError(f"[❌] Whisper transcription failed: {e}")

    words = []
    for segment in result.get("segments", []):
        words.extend(segment.get("words", []))

    if not words:
        raise ValueError("[❌] No words found in Whisper transcription.")

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

        subtitles.append(srt.Subtitle(
            index=index,
            start=timedelta(seconds=start),
            end=timedelta(seconds=end),
            content=text
        ))

        last_end_time = end
        index += 1
        i += words_per_line

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(srt.compose(subtitles))

    logger.info(f"[✅] Generated Whisper SRT for '{category}' → {output_path}")
    update_progress(task_id, "✅ Subtitles ready (Whisper)", 55)

    # Detect Hindi and convert SRT → ASS
    all_text = " ".join(sub.content for sub in subtitles)
    if any('\u0900' <= c <= '\u097F' for c in all_text):
        ass_path = output_path.replace(".srt", ".ass")
        convert_srt_to_ass(output_path, ass_path, font="Noto Sans Devanagari")
        logger.info(f"[🈶] Detected Hindi — ASS subtitle created: {ass_path}")


def convert_srt_to_ass(srt_path: str, ass_path: str, font: str = "Noto Sans Devanagari", fontsize: int = 18) -> None:
    """
    Convert .srt subtitle file to .ass format with font support for Hindi.

    Args:
        srt_path (str): Input SRT file path.
        ass_path (str): Output ASS file path.
        font (str): Font name to use.
        fontsize (int): Font size in points.
    """
    with open(srt_path, "r", encoding="utf-8") as f:
        subs = list(srt.parse(f.read()))

    def format_time(t: timedelta) -> str:
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

    logger.info(f"[🈶] Converted SRT → ASS → {ass_path}")


# CLI entry point for manual testing
if __name__ == "__main__":
    import sys
    if len(sys.argv) not in (3, 4):
        print("Usage: python utils/gen_subtitles.py <category> <audio_path> [language]")
    else:
        category = sys.argv[1]
        audio_file = sys.argv[2]
        lang = sys.argv[3] if len(sys.argv) == 4 else "auto"
        output_srt = os.path.splitext(audio_file)[0] + ".srt"
        generate_srt_from_audio(category, audio_file, output_srt, language=lang)

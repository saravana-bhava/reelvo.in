# ================================================
# File:         utils/generate_srt_from_audio.py
# Description:  Create subtitles from audio
# Framework:    Flask + TailwindCSS
# Version:      1.0.0
# Last Updated: 12 August 2025
# Author:       Saravana Bhava
# Author URL:   https://SazM.in
# ================================================

"""
Subtitle generator using Whisper.

Generates:
- .srt subtitle file for Instagram Reels.
- Automatically converts .srt → .ass for Hindi (Devanagari) subtitle support.
"""

import os
import torch
import srt
import whisper
import warnings
import logging
from datetime import timedelta

from tqdm import tqdm
tqdm(disable=True)

# Prevent Torch Dynamo / FX from dumping bytecode
os.environ.pop("TORCH_LOGS", None)
os.environ.pop("TORCHDYNAMO_VERBOSE", None)

# Completely disable TorchDynamo
if hasattr(torch, "_dynamo"):
    torch._dynamo.config.suppress_errors = True
    torch._dynamo.config.verbose = False
    torch._dynamo.disable()

# Optional progress UI support
try:
    from utils.progress_tracker import update_progress
except ImportError:
    def update_progress(task_id, status, percent): pass

# Logging setup
logger = logging.getLogger("subtitle_gen")
if not logger.hasHandlers():
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Silence Whisper warnings and logs
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")
logging.getLogger("whisper").setLevel(logging.WARNING)

# Load Whisper model once
try:
    MODEL = whisper.load_model("small")
except Exception as e:
    logger.error(f"[❌] Failed to load Whisper model: {e}")
    MODEL = None


def generate_srt_from_audio(
    srt_path: str,
    language: str,
    audio_path: str,
    words_per_line: int = 6,
    task_id: str = "Subtitles"
) -> None:
    """
    Generate SRT subtitle using Whisper transcription.

    Args:
        srt_path (str): Path to save .srt file.
        language (str): 'en', 'hi', or 'auto'.
        audio_path (str): Input audio path.
        words_per_line (int): Number of words per subtitle line.
    """
    if not MODEL:
        raise RuntimeError("[❌] Whisper model not loaded. Cannot generate subtitles.")

    if not os.path.isfile(audio_path):
        raise FileNotFoundError(f"[❌] Audio file not found: {audio_path}")

    logger.info(f"[🧠] Transcribing audio → {audio_path}")

    try:
        result = MODEL.transcribe(
            audio_path,
            word_timestamps=True,
            language=language,
            verbose=False
        )
    except Exception as e:
        raise RuntimeError(f"[❌] Whisper transcription failed: {e}")

    words = [w for seg in result.get("segments", []) for w in seg.get("words", [])]
    if not words:
        raise ValueError("[❌] No words found in Whisper transcription.")

    subtitles = []
    index = 1
    min_duration = 1.5
    max_duration = 4.0
    min_gap = 0.1
    last_end_time = 0.5

    total_chunks = (len(words) + words_per_line - 1) // words_per_line

    for i in range(0, len(words), words_per_line):
        chunk = words[i:i + words_per_line]
        if not chunk:
            break

        text = " ".join(w["word"].strip() for w in chunk).replace("  ", " ")
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
            content=text.strip()
        ))

        last_end_time = end
        index += 1

        # Only update progress every 5 subtitles or at 100%
        percent = min(100, int((index - 1) / total_chunks * 100))
        if index % 5 == 0 or percent >= 100:
            update_progress(task_id, f"Processing voice {index - 1}/{total_chunks}", percent)

    os.makedirs(os.path.dirname(srt_path), exist_ok=True)
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(srt.compose(subtitles))

    logger.info(f"[✅] SRT saved → {srt_path}")

    # Check for Hindi script (Devanagari Unicode block)
    combined_text = " ".join(sub.content for sub in subtitles)
    if any('\u0900' <= c <= '\u097F' for c in combined_text):
        ass_path = os.path.splitext(srt_path)[0] + ".ass"
        convert_srt_to_ass(srt_path, ass_path, font="Noto Sans Devanagari")
        logger.info(f"[🈶] ASS generated for Hindi → {ass_path}")


def convert_srt_to_ass(srt_path: str, ass_path: str, font: str = "Noto Sans Devanagari", fontsize: int = 18) -> None:
    with open(srt_path, "r", encoding="utf-8") as f:
        subs = list(srt.parse(f.read()))

    def format_time(t: timedelta) -> str:
        total_cs = int(t.total_seconds() * 100)
        h = total_cs // 360000
        m = (total_cs % 360000) // 6000
        s = (total_cs % 6000) // 100
        cs = total_cs % 100
        return f"{h}:{m:02}:{s:02}.{cs:02}"

    ass_header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
Collisions: Normal
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font},{fontsize},&H00FFFFFF,&H80000000,1,2,0,2,10,10,100,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    ass_events = "".join(
        f"Dialogue: 0,{format_time(sub.start)},{format_time(sub.end)},Default,,0,0,0,,{sub.content.replace(chr(10),' ')}\n"
        for sub in subs
    )

    os.makedirs(os.path.dirname(ass_path), exist_ok=True)
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_header + ass_events)

    logger.info(f"[🈶] Converted {srt_path} → {ass_path}")


# CLI usage
if __name__ == "__main__":
    import sys

    if len(sys.argv) not in (3, 4):
        print("Usage: python utils/generate_srt_from_audio.py <audio_path> <srt_output_path> [language]")
        sys.exit(1)

    audio_path = sys.argv[1]
    srt_output_path = sys.argv[2]
    language = sys.argv[3] if len(sys.argv) == 4 else "auto"

    try:
        generate_srt_from_audio(
            srt_path=srt_output_path,
            language=language,
            audio_path=audio_path,
            words_per_line=6
        )
    except Exception as e:
        logger.error(f"[💥] Subtitle generation failed: {e}")
        sys.exit(1)

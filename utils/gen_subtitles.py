# utils/gen_subtitles.py

import os
from datetime import timedelta

def to_srt_timestamp(seconds: float) -> str:
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = int(td.microseconds / 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

def generate_srt_from_file(category: str, output_dir="output", duration=10.0):
    input_path = os.path.join(output_dir, f"{category}_text.txt")
    srt_path = os.path.join(output_dir, f"{category}.srt")

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"[❌] Text file not found: {input_path}")

    with open(input_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    if not lines:
        raise ValueError("Script file is empty.")

    duration_per_line = duration / len(lines)
    srt_content = ""

    for i, line in enumerate(lines):
        start = to_srt_timestamp(i * duration_per_line)
        end = to_srt_timestamp(min((i + 1) * duration_per_line, duration))
        srt_content += f"{i + 1}\n{start} --> {end}\n{line}\n\n"

    os.makedirs(output_dir, exist_ok=True)
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(srt_content.strip())

    print(f"[✅] Generated SRT for '{category}' → {srt_path}")

if __name__ == "__main__":
    import sys

    if len(sys.argv) == 2:
        generate_srt_from_file(sys.argv[1])
    elif len(sys.argv) == 3:
        category = sys.argv[1]
        duration = float(sys.argv[2])
        generate_srt_from_file(category, duration=duration)
    else:
        print("Usage: python utils/gen_subtitles.py <category> [duration]")
        print("Example: python utils/gen_subtitles.py motivation 10")

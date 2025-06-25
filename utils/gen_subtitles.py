# utils/gen_subtitles.py

import os
import subprocess
import whisper
import srt
from datetime import timedelta

def generate_srt_from_audio(category: str, audio_path: str, output_path: str):
    print(f"[🧠] Transcribing audio for word-level subtitles: {audio_path}")
    model = whisper.load_model("base")
    result = model.transcribe(audio_path, word_timestamps=True)

    index = 1
    subtitles = []
    for segment in result['segments']:
        for word in segment['words']:
            start = timedelta(seconds=word['start'])
            end = timedelta(seconds=word['end'])
            content = word['word'].strip()
            if content:
                subtitles.append(srt.Subtitle(index, start, end, content))
                index += 1

    srt_output = srt.compose(subtitles)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(srt_output)
    print(f"[✅] Generated SRT for '{category}' → {output_path}")

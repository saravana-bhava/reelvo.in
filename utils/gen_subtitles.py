import os
import whisper
import srt
import re
from datetime import timedelta

def split_into_sentences(text):
    # Basic split on punctuation
    return re.split(r'(?<=[.!?])\s+', text.strip())

def generate_srt_from_audio(category: str, audio_path: str, output_path: str):
    print(f"[🧠] Transcribing audio for word-aligned sentences: {audio_path}")
    model = whisper.load_model("base")
    result = model.transcribe(audio_path, word_timestamps=True)

    words = []
    for segment in result["segments"]:
        words.extend(segment.get("words", []))

    full_text = result["text"]
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

        # Try to match sentence_words in words[]
        while word_idx + match_len <= len(words):
            chunk = words[word_idx:word_idx + match_len]
            chunk_text = " ".join(w["word"].strip() for w in chunk)
            if chunk_text.replace("’", "'") == sentence.replace("’", "'"):
                matched_words = chunk
                break
            word_idx += 1

        if not matched_words:
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
        word_idx += match_len  # move pointer forward

    # Save SRT
    srt_output = srt.compose(subtitles)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(srt_output)
    print(f"[✅] Generated word-aligned SRT for '{category}' → {output_path}")

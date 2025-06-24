# create_video.py

import os
import subprocess
from dotenv import load_dotenv
from utils.gen_text_overlay import generate_text_overlay
from utils.gen_tts_audio import generate_tts_from_file
from utils.gen_subtitles import generate_srt_from_file

load_dotenv()

# Paths
OUTPUT_DIR = "fallback"
IMAGE_DIR = "assets/images"
AUDIO_DIR = "output"
TEXT_IMG_DIR = "output"
SRT_DIR = "output"
VIDEO_DIR = "assets/videos"

CATEGORIES = ["motivation", "success", "life", "inspiration", "sad"]
VIDEO_DURATION = 10  # seconds

def create_video_for_category(category):
    print(f"\n🎬 Generating reel for: {category.upper()}")

    text_path = f"{TEXT_IMG_DIR}/{category}_text.txt"
    image_path = f"{IMAGE_DIR}/{category}.png"
    audio_path = f"{AUDIO_DIR}/{category}.mp3"
    text_image_path = f"{TEXT_IMG_DIR}/{category}_text.png"
    srt_path = f"{SRT_DIR}/{category}.srt"
    stock_video_path = f"{VIDEO_DIR}/{category}.mp4"
    output_path = f"{OUTPUT_DIR}/{category}.mp4"

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs("output", exist_ok=True)

    if not os.path.exists(text_path):
        print(f"[❌] Missing script text: {text_path}")
        return

    with open(text_path, "r") as f:
        script = f.read().strip()

    try:
        generate_text_overlay(script, text_image_path)
    except Exception as e:
        print(f"[❌] Failed generating text overlay: {e}")
        return

    try:
        generate_tts_from_file(category)
    except Exception as e:
        print(f"[❌] Failed TTS generation: {e}")
        return

    try:
        generate_srt_from_file(category, duration=VIDEO_DURATION)
    except Exception as e:
        print(f"[❌] Failed subtitle generation: {e}")
        return

    if os.path.exists(stock_video_path):
        print(f"[🎥] Using stock video: {stock_video_path}")
        base_video_input = ["-i", stock_video_path]
    else:
        print(f"[⚠️] Stock video not found. Using black fallback.")
        base_video_input = ["-f", "lavfi", "-t", str(VIDEO_DURATION), "-i", "color=c=black:s=1080x1920"]

    ffmpeg_cmd = [
        "ffmpeg",
        *base_video_input,
        "-loop", "1", "-i", image_path,
        "-loop", "1", "-i", text_image_path,
        "-i", audio_path,
        "-filter_complex",
        "[0:v][1:v]overlay=0:0[tmp1];[tmp1][2:v]overlay=(W-w)/2:(H-h)/2[outv]",
        "-map", "[outv]", "-map", "3:a",
        "-t", str(VIDEO_DURATION),
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "28",
        "-c:a", "aac",
        "-pix_fmt", "yuv420p",
        "-y", output_path
    ]

    try:
        subprocess.run(ffmpeg_cmd, check=True)
        print(f"[✅] Final reel generated: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"[❌] FFmpeg failed: {e}")

if __name__ == "__main__":
    for category in CATEGORIES:
        create_video_for_category(category)

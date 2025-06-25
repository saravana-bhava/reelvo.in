# create_video.py

import os
import subprocess
from dotenv import load_dotenv
from utils.gen_text_overlay import generate_text_overlay
from utils.gen_tts_audio import generate_tts_from_file
from utils.gen_subtitles import generate_srt_from_audio

load_dotenv()

# Paths
OUTPUT_DIR = "fallback"
IMAGE_DIR = "assets/images"
AUDIO_DIR = "output"
TEXT_IMG_DIR = "output"
SRT_DIR = "output"
VIDEO_DIR = "assets/videos"
TEXT_DIR = "output"

CATEGORIES = ["motivation", "success", "life", "inspiration", "sad"]
VIDEO_DURATION = 10  # seconds

def create_video_for_category(category):
    print(f"\n🎬 Generating reel for: {category.upper()}")

    text_path = f"{TEXT_DIR}/{category}_text.txt"
    image_path = f"{IMAGE_DIR}/{category}.png"
    audio_path = f"{AUDIO_DIR}/{category}.mp3"
    text_image_path = f"{TEXT_IMG_DIR}/{category}_text.png"
    srt_path = f"{SRT_DIR}/{category}.srt"
    stock_video_path = f"{VIDEO_DIR}/{category}.mp4"
    output_path = f"{OUTPUT_DIR}/{category}.mp4"

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if not os.path.exists(text_path):
        print(f"[❌] Missing script text: {text_path}")
        return

    with open(text_path, "r") as f:
        script = f.read().strip()

    try:
        generate_text_overlay(script, text_image_path)
        generate_tts_from_file(category)
        generate_srt_from_audio(category, audio_path, srt_path)
    except Exception as e:
        print(f"[❌] Asset generation failed: {e}")
        return

    use_video = os.path.exists(stock_video_path)
    use_image = not use_video and os.path.exists(image_path)
    use_text_overlay = not use_video and not use_image

    inputs = []
    filters = []
    input_count = 0

    if use_video:
        print(f"[🎥] Using stock video: {stock_video_path}")
        inputs += ["-i", stock_video_path]
        filters.append(f"[0:v]fade=t=in:st=0:d=1,fade=t=out:st=9:d=1[tmp1]")
    else:
        print(f"[🪄] Using black background fallback")
        inputs += ["-f", "lavfi", "-t", str(VIDEO_DURATION), "-i", "color=c=black:s=1080x1920"]
        filters.append(f"[0:v]fade=t=in:st=0:d=1,fade=t=out:st=9:d=1[tmp1]")

    if use_image:
        print(f"[🖼️] Using image overlay: {image_path}")
        inputs += ["-loop", "1", "-i", image_path]
        filters.append(f"[tmp1][1:v]overlay=(W-w)/2:(H-h)/2:enable='between(t,0,10)'[tmp2]")
        overlay_output = "[tmp2]"
        input_count = 2
    elif use_text_overlay:
        print(f"[🖋️] Using text overlay: {text_image_path}")
        inputs += ["-loop", "1", "-i", text_image_path]
        filters.append(f"[tmp1][1:v]overlay=(W-w)/2:(H-h)/2:enable='between(t,0,10)'[tmp2]")
        overlay_output = "[tmp2]"
        input_count = 2
    else:
        overlay_output = "[tmp1]"
        input_count = 1

    # Add subtitles
    filters.append(f"{overlay_output}subtitles='{srt_path}':force_style='FontSize=28,PrimaryColour=&HFFFFFF&'[outv]")

    # Add audio
    inputs += ["-i", audio_path]  # audio is always last

    cmd = [
        "ffmpeg", *inputs,
        "-filter_complex", ";".join(filters),
        "-map", "[outv]",
        "-map", f"{input_count}:a",  # audio is at this index
        "-t", str(VIDEO_DURATION),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "28",
        "-c:a", "aac", "-shortest",
        "-pix_fmt", "yuv420p",
        "-y", output_path
    ]

    try:
        subprocess.run(cmd, check=True)
        print(f"[✅] Final reel generated: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"[❌] FFmpeg failed: {e}")

if __name__ == "__main__":
    for category in CATEGORIES:
        create_video_for_category(category)

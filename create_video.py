# create_video.py

import os
import subprocess
from dotenv import load_dotenv
from utils.gen_text_overlay import generate_text_overlay
from utils.gen_tts_audio import generate_tts_from_file
from utils.gen_subtitles import generate_srt_from_audio

load_dotenv()

IMAGE_DIR = "assets/images"
VIDEO_DIR = "assets/videos"

CATEGORIES = ["motivation", "success", "life", "inspiration", "sad"]
VIDEO_DURATION = 10  # seconds


def create_video_for_category(category, username):
    print(f"\n🎬 Generating reel for: {category.upper()} | User: {username}")

    base_output = os.path.join("output", username)
    os.makedirs(base_output, exist_ok=True)

    text_path = os.path.join(base_output, f"{category}_text.txt")
    audio_path = os.path.join(base_output, f"{category}.mp3")
    text_image_path = os.path.join(base_output, f"{category}_text.png")
    srt_path = os.path.join(base_output, f"{category}.srt")
    output_path = os.path.join(base_output, f"{category}.mp4")

    image_path = f"assets/images/{category}.png"
    stock_video_path = f"assets/videos/{category}.mp4"

    if not os.path.exists(text_path):
        print(f"[❌] Missing script text: {text_path}")
        return None

    with open(text_path, "r") as f:
        script = f.read().strip()

    try:
        from utils.gen_text_overlay import generate_text_overlay
        from utils.gen_tts_audio import generate_tts_from_file
        from utils.gen_subtitles import generate_srt_from_audio

        generate_text_overlay(script, text_image_path)
        generate_tts_from_file(category, base_output)
        generate_srt_from_audio(category, audio_path, srt_path)
    except Exception as e:
        print(f"[❌] Asset generation failed: {e}")
        return None

    use_video = os.path.exists(stock_video_path)
    use_image = not use_video and os.path.exists(image_path)
    use_text_overlay = not use_video and not use_image

    inputs = []
    filters = []
    input_count = 0

    # Input 0: video or fallback
    if use_video:
        print(f"[🎥] Using stock video: {stock_video_path}")
        inputs += ["-i", stock_video_path]
    else:
        print(f"[🪄] Using black background fallback")
        inputs += ["-f", "lavfi", "-t", "10", "-i", "color=c=black:s=1080x1920"]

    # Input 1: overlay image
    if use_image:
        print(f"[🖼️] Using image overlay: {image_path}")
        inputs += ["-loop", "1", "-i", image_path]
        filters.append(f"[0:v][1:v]overlay=(W-w)/2:(H-h)/2:enable='between(t,0,10)'[base]")
        input_count = 2
    elif use_text_overlay:
        print(f"[🖋️] Using text overlay: {text_image_path}")
        inputs += ["-loop", "1", "-i", text_image_path]
        filters.append(f"[0:v][1:v]overlay=(W-w)/2:(H-h)/2:enable='between(t,0,10)'[base]")
        input_count = 2
    else:
        filters.append("[0:v]fade=t=in:st=0:d=1,fade=t=out:st=9:d=1[base]")
        input_count = 1

    # Input 2: audio
    inputs += ["-i", audio_path]

    # Add subtitles using SRT file (overlay on 'base')
    filters.append(f"[base]subtitles='{srt_path}':force_style='FontSize=28,PrimaryColour=&HFFFFFF&'[outv]")

    cmd = [
        "ffmpeg", *inputs,
        "-filter_complex", ";".join(filters),
        "-map", "[outv]",
        "-map", f"{input_count}:a",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "28",
        "-c:a", "aac", "-shortest",
        "-pix_fmt", "yuv420p",
        "-y", output_path
    ]

    try:
        subprocess.run(cmd, check=True)
        print(f"[✅] Final reel generated: {output_path}")
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"[❌] FFmpeg failed: {e}")
        return None


# CLI usage
if __name__ == "__main__":
    import sys
    if len(sys.argv) == 3:
        category, username = sys.argv[1], sys.argv[2]
        create_video_for_category(category, username)
    else:
        print("Usage: python create_video.py <category> <username>")

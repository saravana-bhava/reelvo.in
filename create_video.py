# create_video.py

import os
import subprocess
from dotenv import load_dotenv
from datetime import timedelta
import srt

from utils.gen_text_overlay import generate_text_overlay
from utils.gen_tts_audio import generate_tts_from_file
from utils.gen_subtitles import generate_srt_from_audio
from utils.generate_script import generate_script_for_user
from utils.pixabay_video import fetch_pixabay_video
from utils.pexels_video import try_pexels_fallback

load_dotenv()

IMAGE_DIR = "assets/images"
VIDEO_DIR = "assets/videos"
WATERMARK_PATH = "assets/logo.png"
VIDEO_DURATION = 30
CATEGORIES = ["motivation", "success", "life", "inspiration", "sad"]

USE_PIXABAY = os.getenv("USE_PIXABAY", "true").lower() == "true"
USE_PEXELS = os.getenv("USE_PEXELS", "false").lower() == "true"

def clip_srt_timing(srt_path, start=0.5, end=29.5):
    with open(srt_path, 'r', encoding='utf-8') as f:
        subs = list(srt.parse(f.read()))

    clipped = []
    for sub in subs:
        s = max(sub.start.total_seconds(), start)
        e = min(sub.end.total_seconds(), end)
        if s < e:
            sub.start = timedelta(seconds=s)
            sub.end = timedelta(seconds=e)
            clipped.append(sub)

    with open(srt_path, 'w', encoding='utf-8') as f:
        f.write(srt.compose(clipped))

def create_video_for_category(category, username):
    print(f"\n🎬 Generating reel for: {category.upper()} | User: {username}")
    base_output = os.path.join("output", username)
    os.makedirs(base_output, exist_ok=True)

    text_path = generate_script_for_user(category, username)
    if not os.path.exists(text_path):
        print(f"[❌] Failed to generate script for {category}")
        return None

    audio_path = os.path.join(base_output, f"{category}.mp3")
    text_image_path = os.path.join(base_output, f"{category}_text.png")
    srt_path = os.path.join(base_output, f"{category}.srt")
    output_path = os.path.join(base_output, f"{category}.mp4")

    image_path = os.path.join(IMAGE_DIR, f"{category}.png")
    stock_video_path = os.path.join("temp", f"{category}_stock.mp4")
    fallback_local_video = os.path.join(VIDEO_DIR, f"{category}.mp4")

    # Step 1: Try Pexels
    downloaded = False
    if USE_PEXELS:
        downloaded = try_pexels_fallback(category, stock_video_path)

    # Step 2: Try Pixabay if Pexels failed
    if not downloaded and USE_PIXABAY:
        downloaded = fetch_pixabay_video(category, stock_video_path)

    # Step 3: Local fallback if both failed
    if not downloaded:
        if os.path.exists(fallback_local_video):
            print(f"[🧩] Falling back to local video: {fallback_local_video}")
            stock_video_path = fallback_local_video
        else:
            print("[⚠️] No stock video found. Using black background.")
            stock_video_path = None

    with open(text_path, "r") as f:
        script = f.read().strip()

    try:
        generate_text_overlay(script, text_image_path)
        generate_tts_from_file(category, username)
        generate_srt_from_audio(category, audio_path, srt_path)
    except Exception as e:
        print(f"[❌] Asset generation failed: {e}")
        return None

    clip_srt_timing(srt_path, 0.5, 29.5)

    inputs, filters = [], []
    input_index = 0

    # Background video or fallback
    if stock_video_path and os.path.exists(stock_video_path):
        inputs += ["-i", stock_video_path]
        print(f"[🎥] Using stock video: {stock_video_path}")
    else:
        inputs += ["-f", "lavfi", "-t", str(VIDEO_DURATION), "-i", "color=c=black:s=1080x1920"]
        print("[🪄] Using fallback black background")
    input_index += 1

    # Overlay if black bg used
    overlay_used = False
    if not stock_video_path or not os.path.exists(stock_video_path):
        if os.path.exists(image_path):
            overlay_path = image_path
            print(f"[🖼️] Using image overlay: {overlay_path}")
        elif os.path.exists(text_image_path):
            overlay_path = text_image_path
            print(f"[🖋️] Using text overlay: {overlay_path}")
        else:
            print(f"[⚠️] No overlay image found.")
            return None
        inputs += ["-loop", "1", "-t", str(VIDEO_DURATION), "-i", overlay_path]
        overlay_used = True
        overlay_index = input_index
        input_index += 1

    # Audio
    inputs += ["-i", audio_path]
    audio_input_index = input_index
    input_index += 1

    # Watermark
    use_logo = os.path.exists(WATERMARK_PATH)
    if use_logo:
        inputs += ["-loop", "1", "-t", str(VIDEO_DURATION), "-i", WATERMARK_PATH]
        logo_index = input_index
        print(f"[🔖] Using watermark: {WATERMARK_PATH}")
        input_index += 1

    # Filters
    filters.append(
        f"[0:v]scale=1080:1920:force_original_aspect_ratio=decrease,"
        f"pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1,"
        f"fade=t=in:st=0:d=1,fade=t=out:st={VIDEO_DURATION-1}:d=1[bg]"
    )
    base_stream = "[bg]"

    if overlay_used:
        filters.append(
            f"{base_stream}[{overlay_index}:v]overlay=(W-w)/2:(H-h)/2:enable='between(t,0,{VIDEO_DURATION})'[mid]"
        )
        base_stream = "[mid]"

    if use_logo:
        filters.append(
            f"{base_stream}[{logo_index}:v]overlay=W-w-30:H-h-30[wm]"
        )
        base_stream = "[wm]"

    filters.append(
        f"{base_stream}drawbox=x=0:y=0:w=iw:h=200:color=black@0.4:t=fill,"
        f"drawbox=x=0:y=ih-200:w=iw:h=200:color=black@0.4:t=fill[boxed]"
    )

    subtitle_style = (
        "FontName=DejaVuSans-Bold,"
        "FontSize=25,"
        "PrimaryColour=&H00FFFFFF&,"
        "OutlineColour=&H000000&,"
        "BorderStyle=1,"
        "Outline=2,"
        "Shadow=0,"
        "MarginV=100,"
        "Alignment=2"
    )
    filters.append(f"[boxed]subtitles='{srt_path}':force_style='{subtitle_style}'[outv]")

    cmd = [
        "ffmpeg", *inputs,
        "-filter_complex", ";".join(filters),
        "-map", "[outv]",
        "-map", f"{audio_input_index}:a",
        "-c:v", "libx264", "-preset", "slow", "-crf", "18",
        "-b:v", "10M", "-minrate", "8M", "-maxrate", "12M", "-bufsize", "12M",
        "-c:a", "aac", "-ar", "44100", "-b:a", "256k", "-ac", "2",
        "-movflags", "+faststart",
        "-pix_fmt", "yuv420p",
        "-r", "30",
        "-y", output_path
    ]

    print(f"[📦] Running FFmpeg command:\n{' '.join(cmd)}")

    try:
        subprocess.run(cmd, check=True)
        print(f"[✅] Final reel generated: {output_path}")
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"[❌] FFmpeg failed: {e}")
        return None

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 3:
        create_video_for_category(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python create_video.py <category> <username>")

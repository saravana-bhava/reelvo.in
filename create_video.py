# create_video.py

import os
import subprocess
import random
from dotenv import load_dotenv
from datetime import timedelta
import srt

from utils.gen_text_overlay import generate_text_overlay
from utils.gen_tts_audio import generate_tts_from_file
from utils.gen_subtitles import generate_srt_from_audio
from utils.generate_script import generate_script_for_user
from utils.pixabay_video import fetch_pixabay_video
from utils.pexels_video import try_pexels_fallback
from utils.video_utils import download_video, get_video_duration

load_dotenv()

IMAGE_DIR = "assets/images"
VIDEO_DIR = "assets/videos"
TEMP_DIR = "temp"
WATERMARK_PATH = "assets/logo.png"
VIDEO_DURATION = 30
CLIP_COUNT = 5  # 5 clips of ~6s to form 30s
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

def fetch_multiple_clips(category, count=5):
    downloaded_clips = []
    used_urls = set()
    sources = [try_pexels_fallback, fetch_pixabay_video]
    fallback_local = os.path.join(VIDEO_DIR, f"{category}.mp4")

    for i in range(count):
        clip_path = os.path.join(TEMP_DIR, f"{category}_clip{i+1}.mp4")
        for source in sources:
            if source == try_pexels_fallback and USE_PEXELS:
                if try_pexels_fallback(category, clip_path, used_urls=used_urls):
                    downloaded_clips.append(clip_path)
                    break
            elif source == fetch_pixabay_video and USE_PIXABAY:
                if fetch_pixabay_video(category, clip_path, used_urls=used_urls):
                    downloaded_clips.append(clip_path)
                    break
        else:
            if os.path.exists(fallback_local):
                downloaded = download_video(fallback_local, clip_path, min_duration=5, max_duration=6)
                if downloaded:
                    downloaded_clips.append(clip_path)

    return downloaded_clips

def concatenate_clips(clips, output_path):
    list_file = os.path.join(TEMP_DIR, "concat_list.txt")
    with open(list_file, "w") as f:
        for clip in clips:
            f.write(f"file '{os.path.abspath(clip)}'\n")

    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file,
        "-c", "copy", output_path
    ]
    subprocess.run(cmd, check=True)
    return output_path

def create_video_for_category(category, username):
    print(f"\n🎬 Generating reel for: {category.upper()} | User: {username}")
    base_output = os.path.join("output", username)
    os.makedirs(base_output, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)

    text_path = generate_script_for_user(category, username)
    if not os.path.exists(text_path):
        print(f"[❌] Failed to generate script for {category}")
        return None

    audio_path = os.path.join(base_output, f"{category}.mp3")
    text_image_path = os.path.join(base_output, f"{category}_text.png")
    srt_path = os.path.join(base_output, f"{category}.srt")
    final_output_path = os.path.join(base_output, f"{category}.mp4")

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

    clips = fetch_multiple_clips(category, CLIP_COUNT)
    if not clips:
        print("[❌] No background clips found.")
        return None

    combined_video_path = os.path.join(TEMP_DIR, f"{category}_combined.mp4")
    concatenate_clips(clips, combined_video_path)

    inputs = ["-i", combined_video_path, "-i", audio_path]
    input_index = 2

    if os.path.exists(WATERMARK_PATH):
        inputs += ["-loop", "1", "-t", str(VIDEO_DURATION), "-i", WATERMARK_PATH]
        logo_index = input_index
        input_index += 1
    else:
        logo_index = None

    filters = [
        f"[0:v]scale=1080:1920:force_original_aspect_ratio=decrease,"
        f"pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1,"
        f"fade=t=in:st=0:d=1,fade=t=out:st={VIDEO_DURATION-1}:d=1[bg]"
    ]

    base_stream = "[bg]"

    if logo_index is not None:
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
        "FontSize=20,"
        "PrimaryColour=&H00FFFFFF&,"
        "OutlineColour=&H000000&,"
        "BorderStyle=1,"
        "Outline=1,"
        "Shadow=0,"
        "MarginV=50,"
        "Alignment=2"
    )
    filters.append(f"[boxed]subtitles='{srt_path}':force_style='{subtitle_style}'[outv]")

    cmd = [
        "ffmpeg", *inputs,
        "-filter_complex", ";".join(filters),
        "-map", "[outv]",
        "-map", "1:a",
        "-c:v", "libx264", "-preset", "slow", "-crf", "18",
        "-b:v", "10M", "-minrate", "8M", "-maxrate", "12M", "-bufsize", "12M",
        "-c:a", "aac", "-ar", "44100", "-b:a", "256k", "-ac", "2",
        "-movflags", "+faststart",
        "-pix_fmt", "yuv420p",
        "-r", "30",
        "-y", final_output_path
    ]

    print(f"[📦] Running FFmpeg command:\n{' '.join(cmd)}")

    try:
        subprocess.run(cmd, check=True)
        print(f"[✅] Final reel generated: {final_output_path}")
        return final_output_path
    except subprocess.CalledProcessError as e:
        print(f"[❌] FFmpeg failed: {e}")
        return None

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 3:
        create_video_for_category(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python create_video.py <category> <username>")

import os
import requests
import subprocess
from datetime import datetime

def try_veed_ai(script):
    try:
        api_key = os.getenv("VEED_API_KEY")
        response = requests.post(
            "https://api.veed.io/v1/video/script",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"script": script, "language": "en", "title": "Auto Video"}
        )
        res = response.json()
        if "video_url" in res:
            return res["video_url"], "veed"
        else:
            return None, None
    except Exception as e:
        print("[❌] VEED API error:", e)
        return None, None

def fallback_ffmpeg(script, output_path="output/video.mp4"):
    try:
        print("[ℹ️] Generating fallback video with FFmpeg...")

        os.makedirs("output", exist_ok=True)
        temp_txt_path = "output/text.txt"
        with open(temp_txt_path, "w") as f:
            f.write(script)

        output_path = f"output/reel_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp4"
        command = [
            "ffmpeg",
            "-f", "lavfi",
            "-i", "color=c=black:s=1080x1920:d=10",
            "-vf", f"drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:textfile={temp_txt_path}:fontcolor=white:fontsize=60:x=(w-text_w)/2:y=(h-text_h)/2",
            "-y", output_path
        ]

        subprocess.run(command, check=True)
        return output_path, "ffmpeg"
    except Exception as e:
        print("[❌] FFmpeg fallback error:", e)
        return None, None

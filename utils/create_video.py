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

def fallback_ffmpeg(script, output_path="output/final.mp4"):
    try:
        print("[ℹ️] Using lightweight FFmpeg fallback...")

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        subprocess.run([
            "ffmpeg",
            "-i", "fallback/base.mp4",
            "-c", "copy",
            "-y", output_path
        ], check=True)

        return output_path, "fallback"

    except subprocess.CalledProcessError as e:
        print("[❌] FFmpeg fallback error:", e)
        return None, None

import os
import requests
from moviepy.editor import TextClip, ColorClip, CompositeVideoClip


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


def fallback_moviepy(script, output_path="output/video.mp4"):
    try:
        print("[ℹ️] Generating fallback video with MoviePy...")

        # Background color clip
        background = ColorClip(size=(1080, 1920), color=(20, 20, 20), duration=10)

        # Text Clip with basic settings (no caption_params)
        text = TextClip(
            script,
            fontsize=48,
            font="DejaVu-Sans",
            color="white",
            method="caption",
            size=(1000, None)
        ).set_position("center").set_duration(10)

        # Combine clips
        video = CompositeVideoClip([background, text])

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        video.write_videofile(output_path, fps=24, codec="libx264")

        return output_path, "local"

    except Exception as e:
        print("[❌] MoviePy fallback error:", e)
        return None, None

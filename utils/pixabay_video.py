# utils/pixabay_video.py

import os
import requests
from dotenv import load_dotenv

load_dotenv()

PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY")
PIXABAY_API_URL = "https://pixabay.com/api/videos/"

def fetch_pixabay_video(theme, output_path="temp/bg.mp4"):
    if not PIXABAY_API_KEY:
        raise EnvironmentError("[❌] Missing PIXABAY_API_KEY in .env")

    params = {
        "key": PIXABAY_API_KEY,
        "q": theme,
        "video_type": "film",
        "orientation": "vertical",
        "per_page": 5
    }

    print(f"[🌐] Searching Pixabay for '{theme}' videos...")

    try:
        res = requests.get(PIXABAY_API_URL, params=params, timeout=10)
        res.raise_for_status()
        results = res.json().get("hits", [])
        if not results:
            print("[⚠️] No Pixabay results found.")
            return None

        for result in results:
            for quality in ["large", "medium", "small", "tiny"]:
                video = result.get("videos", {}).get(quality)
                if video and video["width"] == 1080 and video["height"] == 1920:
                    url = video["url"]
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    print(f"[⬇️] Downloading from: {url}")
                    video_data = requests.get(url, stream=True)
                    with open(output_path, "wb") as f:
                        for chunk in video_data.iter_content(1024 * 1024):
                            f.write(chunk)
                    print(f"[✅] Pixabay video saved → {output_path}")
                    return output_path

        print("[⚠️] No 1080x1920 video found on Pixabay.")
        return None

    except Exception as e:
        print(f"[❌] Pixabay error: {e}")
        return None

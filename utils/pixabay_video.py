# utils/pixabay_video.py

import os
import requests
from dotenv import load_dotenv
from utils.video_utils import download_video

load_dotenv()

PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY")
PIXABAY_API_URL = "https://pixabay.com/api/videos/"

def fetch_pixabay_video(theme, output_path, used_urls=None, min_duration=5, max_duration=6):
    if not PIXABAY_API_KEY:
        raise EnvironmentError("[❌] Missing PIXABAY_API_KEY in .env")

    if used_urls is None:
        used_urls = set()

    params = {
        "key": PIXABAY_API_KEY,
        "q": theme,
        "video_type": "film",
        "orientation": "vertical",
        "per_page": 10
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
                    if url in used_urls:
                        continue
                    print(f"[📼] Found 1080x1920 video at: {url}")
                    success = download_video(url, output_path, min_duration, max_duration)
                    if success:
                        used_urls.add(url)
                        return url

        print("[⚠️] No unused 1080x1920 video ≥8s found on Pixabay.")
        return None

    except Exception as e:
        print(f"[❌] Pixabay error: {e}")
        return None

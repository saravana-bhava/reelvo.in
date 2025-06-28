# utils/pixabay_video.py

import os
import requests
from dotenv import load_dotenv
from utils.video_utils import download_video

# Load environment variables
load_dotenv()

PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY")
PIXABAY_API_URL = "https://pixabay.com/api/videos/"

def fetch_pixabay_video(theme, output_path, used_urls=None, min_duration=8, max_duration=12):
    if not PIXABAY_API_KEY:
        raise EnvironmentError("[❌] Missing PIXABAY_API_KEY in .env")

    if used_urls is None:
        used_urls = set()

    params = {
        "key": PIXABAY_API_KEY,
        "q": theme,
        "video_type": "film",
        "orientation": "vertical",
        "per_page": 20  # Increased for more options
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
            duration = result.get("duration", 0)
            if not (min_duration <= duration <= max_duration):
                continue

            for quality in ["large", "medium", "small", "tiny"]:
                video = result.get("videos", {}).get(quality)
                if not video:
                    continue

                width, height = video.get("width"), video.get("height")
                url = video.get("url")

                if width == 1080 and height == 1920 and url and url not in used_urls:
                    print(f"[📼] Pixabay 1080x1920 found: {url} (duration: {duration}s)")
                    success = download_video(url, output_path, min_duration, max_duration)
                    if success:
                        used_urls.add(url)
                        return url

        print("[⚠️] No suitable unused 1080x1920 video (8–12s) found on Pixabay.")
        return None

    except Exception as e:
        print(f"[❌] Pixabay error: {e}")
        return None

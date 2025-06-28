# utils/pexels_video.py

import os
import requests
from dotenv import load_dotenv
from utils.video_utils import download_video

# Load environment
load_dotenv()

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
HEADERS_PEXELS = {"Authorization": PEXELS_API_KEY}

def try_pexels_fallback(category, output_path, used_urls=None, min_duration=8, max_duration=12):
    if not PEXELS_API_KEY:
        print("[❌] Pexels fallback requested but PEXELS_API_KEY is missing.")
        return None

    if used_urls is None:
        used_urls = set()

    print(f"[🔁] Searching Pexels for '{category}'...")

    try:
        response = requests.get(
            "https://api.pexels.com/videos/search",
            headers=HEADERS_PEXELS,
            params={
                "query": category,
                "orientation": "portrait",
                "per_page": 30  # Increase to improve match odds
            },
            timeout=10
        )
        response.raise_for_status()
    except Exception as e:
        print(f"[❌] Pexels API error: {e}")
        return None

    videos = response.json().get("videos", [])
    for video in videos:
        duration = video.get("duration", 0)
        if not (min_duration <= duration <= max_duration):
            continue

        for file in video.get("video_files", []):
            width = file.get("width")
            height = file.get("height")
            url = file.get("link")

            if width == 1080 and height == 1920 and url not in used_urls:
                print(f"[📼] Pexels 1080x1920 found: {url} (duration: {duration}s)")
                success = download_video(url, output_path, min_duration, max_duration)
                if success:
                    used_urls.add(url)
                    return url

    print("[⚠️] No suitable unused 1080x1920 video (8–12s) found on Pexels.")
    return None

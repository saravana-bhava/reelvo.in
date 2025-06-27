# utils/pexels_video.py

import os
import requests
from dotenv import load_dotenv
from utils.video_utils import download_video

load_dotenv()

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

HEADERS_PEXELS = {
    "Authorization": PEXELS_API_KEY
}

def try_pexels_fallback(category, output_path, max_results=5):
    if not PEXELS_API_KEY:
        print("[❌] Pexels fallback requested but PEXELS_API_KEY is missing.")
        return False

    print(f"[🔁] Falling back to Pexels for '{category}'...")

    response = requests.get(
        "https://api.pexels.com/videos/search",
        headers=HEADERS_PEXELS,
        params={
            "query": category,
            "orientation": "portrait",
            "per_page": max_results
        }
    )

    if response.status_code != 200:
        print(f"[❌] Pexels API error: {response.status_code} - {response.text}")
        return False

    data = response.json()
    videos = data.get("videos", [])

    for video in videos:
        for file in video.get("video_files", []):
            if file["width"] >= 720 and file["height"] > file["width"]:  # Vertical format
                return download_video(file["link"], output_path)

    print("[⚠️] No suitable video found on Pexels.")
    return False

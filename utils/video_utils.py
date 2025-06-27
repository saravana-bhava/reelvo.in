# utils/video_utils.py

import requests
import os

def download_video(url, output_path):
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        print(f"[⬇️] Downloading video from: {url}")
        with requests.get(url, stream=True, timeout=15) as r:
            r.raise_for_status()
            with open(output_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)

        print(f"[✅] Video saved → {output_path}")
        return output_path
    except Exception as e:
        print(f"[❌] Failed to download video: {e}")
        return False

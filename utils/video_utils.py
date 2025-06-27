import os
import subprocess
import requests

def get_video_duration(filepath):
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                filepath
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        return float(result.stdout.strip())
    except Exception as e:
        print(f"[❌] Failed to get video duration: {e}")
        return None

def trim_video(input_path, output_path, max_duration=30):
    try:
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", input_path,
                "-t", str(max_duration),
                "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                "-c:a", "aac", "-b:a", "128k",
                output_path
            ],
            check=True
        )
        print(f"[✂️] Trimmed video to {max_duration}s → {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[❌] Failed to trim video: {e}")
        return False

def download_video(url, output_path, max_duration=30):
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        temp_path = output_path + ".tmp"

        print(f"[⬇️] Downloading video from: {url}")
        with requests.get(url, stream=True, timeout=15) as r:
            r.raise_for_status()
            with open(temp_path, 'wb') as f:
                for chunk in r.iter_content(1024 * 1024):
                    f.write(chunk)

        duration = get_video_duration(temp_path)
        if duration is None:
            print("[⚠️] Skipping duration check, saving as-is.")
            os.rename(temp_path, output_path)
            return output_path

        if duration > max_duration:
            print(f"[⏱️] Video is {duration:.2f}s, trimming to {max_duration}s...")
            success = trim_video(temp_path, output_path, max_duration)
            os.remove(temp_path)
            return output_path if success else None
        else:
            os.rename(temp_path, output_path)
            print(f"[✅] Video OK ({duration:.2f}s) → {output_path}")
            return output_path
    except Exception as e:
        print(f"[❌] Failed to download video: {e}")
        return None

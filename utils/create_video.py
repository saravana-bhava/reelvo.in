import os
import subprocess
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def fallback_ffmpeg(script, output_path=None):
    try:
        print("[ℹ️] Using FFmpeg fallback...")

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        output_path = output_path or f"output/reel_{timestamp}.mp4"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        env = os.getenv("ENV", "production").lower()

        if env == "dev":
            # Full FFmpeg with drawtext
            with open("output/text.txt", "w") as f:
                f.write(script.strip())

            command = [
                "ffmpeg",
                "-i", "fallback/base.mp4",
                "-vf", "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:textfile=output/text.txt:fontcolor=white:fontsize=60:x=(w-text_w)/2:y=(h-text_h)/2",
                "-c:a", "copy",
                "-y", output_path
            ]
        else:
            # Lightweight production fallback
            command = [
                "ffmpeg",
                "-i", "fallback/base.mp4",
                "-c", "copy",
                "-y", output_path
            ]

        subprocess.run(command, check=True)
        print("[✅] FFmpeg fallback complete")
        return output_path, "ffmpeg"

    except subprocess.CalledProcessError as e:
        print("[❌] FFmpeg fallback error:", e)
        return None, None

import os
import subprocess
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def fallback_ffmpeg(script, theme="default", output_path=None):
    try:
        print("[ℹ️] Using FFmpeg fallback...")

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        output_path = output_path or f"output/reel_{timestamp}.mp4"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        base_video = f"fallback/{theme.lower()}.mp4"
        if not os.path.exists(base_video):
            print(f"[⚠️] Theme video for '{theme}' not found. Using default fallback.")
            base_video = "fallback/default.mp4"

        env = os.getenv("ENV", "production").lower()

        if env == "dev":
            with open("output/text.txt", "w") as f:
                f.write(script.strip())

            command = [
                "ffmpeg",
                "-i", base_video,
                "-vf", "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:textfile=output/text.txt:fontcolor=white:fontsize=60:x=(w-text_w)/2:y=(h-text_h)/2",
                "-c:a", "copy",
                "-y", output_path
            ]
        else:
            command = [
                "ffmpeg",
                "-i", base_video,
                "-c", "copy",
                "-y", output_path
            ]

        subprocess.run(command, check=True)
        print("[✅] FFmpeg fallback complete")
        return output_path, "ffmpeg"

    except subprocess.CalledProcessError as e:
        print("[❌] FFmpeg fallback error:", e)
        return None, None

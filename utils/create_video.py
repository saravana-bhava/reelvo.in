import os
import subprocess
from datetime import datetime
import httpx
from dotenv import load_dotenv

load_dotenv()

# -------------------- VEED AI (mock/fake fallback) --------------------
def try_veed_ai(script):
    """
    Simulates a VEED.ai API call.
    Replace this with real integration if available.
    """
    print("[ℹ️] Attempting VEED.ai generation...")

    try:
        # Simulated failure (or implement your actual logic here)
        raise Exception("VEED AI not available (simulated)")

        # If successful:
        # return "https://veed.io/generated_video.mp4", "veed"

    except Exception as e:
        print("[❌] VEED AI failed:", e)
        return None, None

# -------------------- Fallback FFmpeg Video Generator --------------------
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

            font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            if not os.path.exists(font_path):
                font_path = "assets/fonts/DejaVuSans-Bold.ttf"

            command = [
                "ffmpeg",
                "-i", base_video,
                "-vf", f"drawtext=fontfile={font_path}:textfile=output/text.txt:fontcolor=white:fontsize=60:x=(w-text_w)/2:y=(h-text_h)/2",
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

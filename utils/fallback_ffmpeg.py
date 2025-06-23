import os
import subprocess
from datetime import datetime

def fallback_ffmpeg_light(script, fallback_base="fallback/base.mp4", output_dir="output"):
    try:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        output_path = os.path.join(output_dir, f"reel_{timestamp}.mp4")
        text_path = os.path.join(output_dir, "text.txt")

        os.makedirs(output_dir, exist_ok=True)

        # Write script to text file
        with open(text_path, "w") as f:
            f.write(script)

        ffmpeg_cmd = [
            "ffmpeg",
            "-i", fallback_base,
            "-vf", (
                f"drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
                f"textfile={text_path}:"
                "fontcolor=white:fontsize=60:"
                "x=(w-text_w)/2:y=(h-text_h)/2"
            ),
            "-c:a", "copy",
            "-y", output_path
        ]

        print("[ℹ️] Generating fallback video with FFmpeg...")
        subprocess.run(ffmpeg_cmd, check=True)

        print(f"[✅] Video saved: {output_path}")
        return output_path, "ffmpeg"

    except Exception as e:
        print("[❌] FFmpeg fallback error:", e)
        return None, None

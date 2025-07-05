# File: utils/generate_text_overlay.py

"""
Generate a text overlay image centered in a vertical canvas.
Supports both English and Hindi script for Instagram Reels.
"""

import os
import logging
from typing import Optional
from PIL import Image, ImageDraw, ImageFont

# Logger setup
logger = logging.getLogger("text_overlay")
logging.basicConfig(level=logging.INFO)

# Constants
CANVAS_WIDTH = 1080
CANVAS_HEIGHT = 1920
FONT_SIZE = 60
MARGIN = 100


def generate_text_overlay(
    text_image_path: str,
    language: str,
    script_text: str
) -> None:
    """
    Generate a vertically centered overlay image with word-wrapped multiline text.

    Args:
        text_image_path (str): Path to save the generated .png/.jpg.
        language (str): Language hint ('en' or 'hi') to auto-select fallback font.
        script_text (str): Text content to render.
    """
    logger.info(f"[🖋️] Rendering text overlay → {text_image_path}")

    if not script_text.strip():
        raise ValueError("[❌] Cannot render empty script text.")

    # Font resolution
    font_path = None
    if language == "hi":
        possible_fonts = [
            "assets/fonts/NotoSansDevanagari-Regular.ttf",
            "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
            "/usr/local/share/fonts/NotoSansDevanagari-Regular.ttf"
        ]
    else:
        possible_fonts = [
            "assets/fonts/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/local/share/fonts/DejaVuSans-Bold.ttf"
        ]

    for path in possible_fonts:
        if os.path.exists(path):
            font_path = path
            break

    if not font_path:
        logger.error(f"[❌] No suitable font found. Tried:\n" + "\n".join(possible_fonts))
        raise FileNotFoundError("No suitable font found. Please install or provide one manually.")

    font = ImageFont.truetype(font_path, FONT_SIZE)

    # Create transparent RGBA canvas
    image = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Word-wrap into lines
    words = script_text.strip().split()
    lines = []
    current_line = ""

    for word in words:
        test_line = f"{current_line} {word}".strip()
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] <= CANVAS_WIDTH - MARGIN:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)

    # Compute vertical centering
    line_height = draw.textbbox((0, 0), "A", font=font)[3] + 18
    total_text_height = line_height * len(lines)
    y = (CANVAS_HEIGHT - total_text_height) // 2

    # Draw each line centered
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        x = (CANVAS_WIDTH - bbox[2]) // 2
        draw.text((x, y), line, font=font, fill="white")
        y += line_height

    # Ensure folder exists
    os.makedirs(os.path.dirname(text_image_path), exist_ok=True)

    # Save as RGB
    image.convert("RGB").save(text_image_path)
    logger.info(f"[✅] Overlay image saved → {text_image_path}")


# CLI usage
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 4:
        print("Usage: python utils/generate_text_overlay.py <text_image_path> <language> <script_text>")
        sys.exit(1)

    text_image_path = sys.argv[1]
    language = sys.argv[2]
    script_text = " ".join(sys.argv[3:])  # Allows multi-word input

    try:
        generate_text_overlay(text_image_path, language, script_text)
        print(f"✅ Saved: {text_image_path}")
    except Exception as e:
        logger.error(f"[❌] Error generating text overlay: {e}")
        sys.exit(1)

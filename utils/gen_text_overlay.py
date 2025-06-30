# File: utils/gen_text_overlay.py

"""
Generate a text overlay image centered in a vertical canvas.
Supports both English and Hindi script for Instagram Reels.
"""

import os
import logging
from typing import Optional
from PIL import Image, ImageDraw, ImageFont

# Logging setup
logger = logging.getLogger("text_overlay")
logging.basicConfig(level=logging.INFO)

# Optional progress UI
try:
    from progress import update_progress
except ImportError:
    def update_progress(task_id: Optional[str], status: str, percent: int): pass


def generate_text_overlay(
    text: str,
    output_path: str,
    width: int = 1080,
    height: int = 1920,
    font_size: int = 60,
    font_path: Optional[str] = None,
    task_id: Optional[str] = None,
    language: str = "en"
) -> None:
    """
    Generate a vertically centered overlay image with word-wrapped multiline text.

    Args:
        text (str): Text content to render.
        output_path (str): Path to save the generated .png/.jpg.
        width (int): Canvas width (default 1080).
        height (int): Canvas height (default 1920).
        font_size (int): Font size for text rendering.
        font_path (Optional[str]): Optional path to a custom .ttf font.
        task_id (Optional[str]): Optional task ID for progress updates.
        language (str): Language hint ('en' or 'hi') to auto-select fallback font.
    """
    update_progress(task_id, "🖋️ Generating text overlay...", 35)
    logger.info(f"[🖋️] Rendering text overlay → {output_path}")

    # Step 1: Font discovery
    if not font_path:
        possible_fonts = (
            [
                "assets/fonts/NotoSansDevanagari-Regular.ttf",
                "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
                "/usr/local/share/fonts/NotoSansDevanagari-Regular.ttf"
            ] if language == "hi" else [
                "assets/fonts/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/local/share/fonts/DejaVuSans-Bold.ttf"
            ]
        )
        for path in possible_fonts:
            if os.path.exists(path):
                font_path = path
                break

    if not font_path or not os.path.exists(font_path):
        logger.error(f"[❌] No suitable font found. Tried:\n{possible_fonts}")
        raise FileNotFoundError(f"No suitable font found. Please install or set path manually.")

    font = ImageFont.truetype(font_path, font_size)

    # Step 2: Create transparent RGBA canvas
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Step 3: Word wrap
    words = text.strip().split()
    lines = []
    line = ""

    for word in words:
        test_line = f"{line} {word}".strip()
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] <= width - 100:  # 50px side padding
            line = test_line
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)

    # Step 4: Vertical centering
    line_height = draw.textbbox((0, 0), "A", font=font)[3] + 15
    total_height = line_height * len(lines)
    y = (height - total_height) // 2

    # Step 5: Draw each line
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        x = (width - bbox[2]) // 2
        draw.text((x, y), line, font=font, fill="white")
        y += line_height

    # Step 6: Save to file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    image.convert("RGB").save(output_path)
    logger.info(f"[✅] Overlay image saved → {output_path}")
    update_progress(task_id, "🖼️ Text overlay ready", 38)


# CLI usage for testing
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python utils/gen_text_overlay.py '<text>' <output_path> [language]")
    else:
        text = sys.argv[1]
        output = sys.argv[2]
        lang = sys.argv[3] if len(sys.argv) > 3 else "en"
        generate_text_overlay(text, output, language=lang)

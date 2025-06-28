# utils/gen_text_overlay.py

import os
from PIL import Image, ImageDraw, ImageFont

# Optional: import progress handler
try:
    from progress import update_progress
except ImportError:
    def update_progress(task_id, status, percent):
        pass

def generate_text_overlay(text, output_path, width=1080, height=1920, font_size=60, font_path=None, task_id=None):
    update_progress(task_id, "🖋️ Generating text overlay...", 35)
    print(f"[🖋️] Generating text overlay image → {output_path}")

    # Default font fallback
    if not font_path:
        possible_fonts = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "assets/fonts/DejaVuSans-Bold.ttf"
        ]
        for path in possible_fonts:
            if os.path.exists(path):
                font_path = path
                break

    if not font_path or not os.path.exists(font_path):
        raise FileNotFoundError(f"[❌] Font not found. Checked: {possible_fonts}")

    # Create transparent canvas
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(font_path, font_size)

    # Wrap text to fit within image width
    words = text.strip().split()
    lines = []
    line = ""

    for word in words:
        test_line = f"{line} {word}".strip()
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] <= width - 100:  # Leave margin
            line = test_line
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)

    # Center text vertically
    line_height = draw.textbbox((0, 0), "A", font=font)[3] + 15
    total_height = line_height * len(lines)
    y = (height - total_height) // 2

    # Draw lines centered horizontally
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        x = (width - bbox[2]) // 2
        draw.text((x, y), line, font=font, fill="white")
        y += line_height

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Save as RGB JPEG for FFmpeg compatibility
    image.convert("RGB").save(output_path)
    print(f"[✅] Overlay image saved → {output_path}")
    update_progress(task_id, "🖼️ Text overlay ready", 38)

# CLI usage
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python utils/gen_text_overlay.py '<text>' <output_path>")
    else:
        generate_text_overlay(sys.argv[1], sys.argv[2])

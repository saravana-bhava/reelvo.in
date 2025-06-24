# utils/gen_text_overlay.py

import os
from PIL import Image, ImageDraw, ImageFont

def generate_text_overlay(text, output_path, width=1080, height=1920, font_size=60, font_path=None):
    print(f"[🖋️] Generating text overlay image → {output_path}")

    # Default font path logic
    if not font_path:
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if not os.path.exists(font_path):
            font_path = "assets/fonts/DejaVuSans-Bold.ttf"
    if not os.path.exists(font_path):
        raise FileNotFoundError(f"[❌] Font not found: {font_path}")

    # Create transparent canvas
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(font_path, font_size)

    # Wrap text into multiple lines that fit within image width
    words = text.strip().split()
    lines = []
    line = ""
    for word in words:
        test_line = f"{line} {word}".strip()
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] <= width - 100:
            line = test_line
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)

    # Calculate vertical centering
    line_height = draw.textbbox((0, 0), "A", font=font)[3] + 15
    total_text_height = line_height * len(lines)
    y = (height - total_text_height) // 2

    # Draw each line centered horizontally
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_width = bbox[2]
        x = (width - line_width) // 2
        draw.text((x, y), line, font=font, fill="white")
        y += line_height

    # Ensure output folder exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Convert to RGB for FFmpeg compatibility and save
    image.convert("RGB").save(output_path)
    print(f"[✅] Overlay image saved to {output_path}")

# CLI usage
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python utils/gen_text_overlay.py '<text>' <output_path>")
    else:
        generate_text_overlay(sys.argv[1], sys.argv[2])

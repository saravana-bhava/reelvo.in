# utils/generate_script.py

import os
from dotenv import load_dotenv
import openai
from openai import OpenAIError, RateLimitError

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise EnvironmentError("[❌] Missing OPENAI_API_KEY in .env")

client = openai.OpenAI(api_key=API_KEY)

FALLBACKS = {
    "motivation": """Push past the pain—growth begins there.
Results shout what effort whispers.
One more step. One more rep. One more win.
Grind in silence—shine in public.""",

    "success": """This isn’t luck—it’s late nights and sacrifice.
Dreams watered with hustle bloom success.
You rise—not by chance, but by choice.
Success is just the beginning.""",

    "life": """Every breath writes your story.
You’re not just living—you’re evolving.
Even chaos is part of the masterpiece.
Live fully. Bloom freely. You’re designed for this.""",

    "inspiration": """Every spark begins in silence.
One thought can start a movement.
Pick up the pen. Begin the change.
The world shifts when you dare to try.""",

    "sad": """Some days are heavier than others.
It’s okay not to be okay right now.
You’ve survived your worst.
Hold on. The light is still coming."""
}

def generate_script(theme: str) -> str:
    prompt = (
        f"Write a short, powerful Instagram reel script on the theme: '{theme}'. "
        f"Format the output in 4-5 impactful lines, under 10 seconds for voice delivery."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{ "role": "user", "content": prompt }],
            temperature=0.7
        )
        text = response.choices[0].message.content.strip()
        print(f"[✅] Script generated via OpenAI for '{theme}'")
        return text

    except RateLimitError:
        print("⚠️ OpenAI Rate Limit hit. Using fallback.")
    except OpenAIError as e:
        print(f"❌ OpenAI error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    # Fallback logic
    return FALLBACKS.get(theme.lower(), f"This is a fallback script for the theme '{theme}'.")

def save_script(theme: str, output_dir="output"):
    text = generate_script(theme)
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, f"{theme}_text.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"[📄] Script saved → {output_path}")
    return output_path

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python utils/generate_script.py <theme>")
    else:
        save_script(sys.argv[1])

# utils/generate_script.py

import os
from dotenv import load_dotenv
import openai
from openai import OpenAIError, RateLimitError
from textwrap import dedent

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise EnvironmentError("[❌] Missing OPENAI_API_KEY in .env")

client = openai.OpenAI(api_key=API_KEY)

FALLBACKS = {
    "motivation": """Push past the pain.
Effort whispers—results shout.
One more step. One more rep.
Grind silent. Shine loud.""",

    "success": """This isn’t luck—it’s hustle.
Dreams bloom with grit.
You rise by choice.
Success starts here.""",

    "life": """Every breath is a story.
You're evolving daily.
Even chaos creates beauty.
Live. Bloom. Become.""",

    "inspiration": """A spark begins in stillness.
One idea moves worlds.
Pick up the pen.
Dare to begin.""",

    "sad": """Some days weigh more.
It's okay to pause.
You’ve survived storms.
Hold on. Light comes."""
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

    return FALLBACKS.get(theme.lower(), f"This is a fallback script for the theme '{theme}'.")

def generate_script_for_user(theme: str, username: str) -> str:
    base_output = os.path.join("output", username)
    os.makedirs(base_output, exist_ok=True)

    output_path = os.path.join(base_output, f"{theme}_text.txt")

    # Use existing script if already generated
    if os.path.exists(output_path):
        print(f"[📝] Script already exists → {output_path}")
        return output_path

    script = generate_script(theme)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(dedent(script).strip())

    print(f"[📄] Script saved → {output_path}")
    return output_path

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python utils/generate_script.py <theme> <username>")
    else:
        theme, username = sys.argv[1], sys.argv[2]
        generate_script_for_user(theme, username)

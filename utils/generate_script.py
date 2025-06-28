# utils/generate_script.py

import os
from dotenv import load_dotenv
import openai
from openai import OpenAIError, RateLimitError
from textwrap import dedent

# Load .env from project root
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(ROOT_DIR, ".env"))

USE_OPENAI = os.getenv("USE_OPENAI", "true").lower() == "true"
API_KEY = os.getenv("OPENAI_API_KEY")

if USE_OPENAI:
    if not API_KEY:
        raise EnvironmentError("[❌] Missing OPENAI_API_KEY in .env")
    client = openai.OpenAI(api_key=API_KEY)
else:
    client = None

FALLBACKS = {
    "motivation": """Every champion starts as a beginner.
You don’t need the full path—just take the first step.
Fall down? Get back up stronger.
Doubt yourself? Do it anyway.
Growth comes from courage, not comfort.
Start now.
You’ve got this.
One day, you’ll thank yourself for not quitting.""",

    "success": """People see the win, not the struggle.
They don’t see the nights you cried or nearly gave up.
But you kept going.
That’s success—showing up, staying strong, rising in silence.
This victory?
It’s built on pain, sacrifice, and belief in yourself.""",

    "life": """Life is messy.
Plans break. People leave.
You cry alone, smile in crowds.
But in pain, there’s power.
Every scar tells a story.
You’re not behind—you’re becoming.
Pause. Breathe.
This chapter is shaping someone stronger than ever before.""",

    "inspiration": """You were born to shine.
The dream inside you matters.
Even if no one sees it—create.
Even if it’s scary—begin.
You have a voice the world hasn’t heard yet.
One spark can light up everything.
Keep going. Your story is just beginning.""",

    "sad": """Some days just hurt.
You smile outside but ache inside.
You miss people. You feel unseen.
But even in silence, healing happens.
It’s okay to cry. It’s okay to feel.
Just don’t give up.
Better days are coming—hold on a little longer."""
}


def generate_script(theme: str) -> str:
    theme = theme.lower()
    if not USE_OPENAI:
        print(f"⚠️ OpenAI disabled (USE_OPENAI=false). Using fallback for '{theme}'")
        return FALLBACKS.get(theme, f"This is a fallback script for the theme '{theme}'.")

    prompt = (
        f"Write a short, powerful Instagram reel script on the theme: '{theme}'. "
        f"Format it into 4–5 impactful lines, under 30 seconds for voice delivery."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{ "role": "user", "content": prompt }],
            temperature=0.7
        )
        script = response.choices[0].message.content.strip()
        print(f"[✅] OpenAI script generated for '{theme}'")
        return script

    except RateLimitError:
        print("⚠️ OpenAI rate limit hit. Using fallback.")
    except OpenAIError as e:
        print(f"[❌] OpenAI error: {e}")
    except Exception as e:
        print(f"[❌] Unexpected error: {e}")

    return FALLBACKS.get(theme, f"This is a fallback script for the theme '{theme}'.")


def generate_script_for_user(theme: str, username: str) -> str:
    base_output = os.path.join("output", username)
    os.makedirs(base_output, exist_ok=True)

    output_path = os.path.join(base_output, f"{theme}_text.txt")

    if os.path.exists(output_path):
        print(f"[📝] Script already exists → {output_path}")
        return output_path

    script = generate_script(theme)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(dedent(script).strip())

    print(f"[📄] Script saved → {output_path}")
    return output_path


# CLI usage
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python utils/generate_script.py <theme> <username>")
    else:
        theme, username = sys.argv[1], sys.argv[2]
        generate_script_for_user(theme, username)

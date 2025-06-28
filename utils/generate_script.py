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
    "motivation": """Every champion started as a beginner who refused to quit.
You don’t need the full map—just the courage to take the first step.
You’ll fall. You’ll doubt yourself. But you’ll rise again.
Growth never comes from staying comfortable.
It comes from pushing through fear and showing up daily.
You’ve got this. Keep going, no matter how slow.
One day, you’ll thank yourself for choosing not to quit when it was hardest to stay.""",

    "success": """People only see the win—they miss what it cost.
They don’t see the late nights, the doubts, the quiet tears.
They don’t hear the voice that said, “Give up,” and the strength that said, “Try again.”
Success isn’t applause—it’s persistence when no one claps.
It’s rising again and again without recognition.
This victory? It’s built on sacrifice, belief, and becoming your own hero first.""",

    "life": """Life doesn’t always follow your plans.
Sometimes it breaks you, reshapes you, rebuilds you.
You laugh with friends, then cry alone—wondering if anyone truly sees you.
But every tear waters something new. Every scar tells a story of survival.
You’re not falling behind. You’re unfolding, evolving, becoming.
So breathe. Be still.
This chapter is not the end—it’s the beginning of someone stronger than ever.""",

    "inspiration": """You weren’t born to blend in—you were born to stand out.
The dream inside you was placed there on purpose.
Even if it’s scary, even if no one believes—start anyway.
Keep creating. Keep believing. The world needs your light.
You’re not too late. You’re not too small.
You are powerful, and you are needed.
Let your voice rise. Let your spark grow.
Your story is just beginning—and it’s worth telling.""",

    "sad": """Some days feel heavier than others.
You smile around people, but ache in silence.
You miss what was. You grieve what never came.
And that’s okay. It’s human to feel deeply.
But even in your quiet pain, healing is working.
You’re not broken—you’re processing.
You’re still here. Still breathing.
Don’t give up yet.
Light always returns, even after the longest dark.""",
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

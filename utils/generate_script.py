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
    "motivation": """Every champion was once a beginner who refused to quit.
You don’t need to have it all figured out—just start.
Your future self is built by what you do today, not someday.
Fall down? Get back up stronger.
Doubt yourself? Do it anyway.
Because growth doesn’t come from comfort—it comes from courage.
So stop waiting.
Start now.
You’ve got this.""",

    "success": """They only see the success… not the sleepless nights.
Not the tears you wiped alone.
Not the days you doubted yourself but kept going anyway.
You’ve been broken, overlooked, and underestimated.
But you kept rising.
Quietly. Relentlessly.
Success isn’t always loud—it’s the strength to keep moving when no one’s clapping.
This victory?
It’s built on pain, perseverance… and silent battles no one knew you fought.""",

    "life": """Life doesn’t always go the way we hoped.
People leave. Promises fade.
And sometimes, it feels like the weight is too much to carry.
You laugh in public, cry in silence, and keep pretending you're fine.
But behind every smile is a story no one sees.
And behind every scar is a lesson life forced you to learn.
It’s okay to feel broken.
It’s okay to slow down.
Just remember—this chapter isn't the end.""",

    "inspiration": """You were not born to blend in—you were made to shine.
Every dream inside you was planted for a reason.
Even if the path is unclear, take the step.
Even if no one believes in you, believe in yourself.
Because one spark of courage can light a fire of purpose.
Keep going.
Keep dreaming.
Your story is just beginning, and the world is waiting for your light.""",

    "sad": """Some days feel heavier than others.
You smile in front of everyone, but inside… it aches.
People say, 'It’ll pass'—but they don’t see the storm within.
You replay memories, wonder what went wrong, and quietly break.
But even in the silence, you’re healing.
Even through the tears, you’re growing.
It’s okay to feel lost.
It’s okay to not be okay.
Just don’t give up—brighter days are still ahead."""
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

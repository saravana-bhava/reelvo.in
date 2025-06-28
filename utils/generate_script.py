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
You don’t need to have all the answers—just take the first step.
Your future isn’t built by luck, it’s built by what you do today.
Fall down? Get back up stronger.
Doubt yourself? Do it anyway.
Growth never comes from comfort—it comes from courage.
So stop waiting.
Take that leap.
You’ve got this.
And one day, you’ll thank yourself for not giving up when it was hardest to keep going.""",

    "success": """People only see the success.
They don’t see the nights you couldn’t sleep, or the times you questioned everything.
The tears no one saw. The moments you almost quit.
But you didn’t.
You rose, quietly, again and again.
Success isn’t trophies or applause—it’s resilience.
It’s showing up when no one’s watching.
It’s fighting silent battles and still finding strength.
This victory?
It’s built on sacrifice, persistence, and believing in yourself long before anyone else did.""",

    "life": """Life can be messy.
Things don’t always go as planned. People leave. Promises break.
You laugh around others and cry alone, wondering if anyone really sees you.
But even in the chaos, there’s growth.
Even in pain, there’s power.
Every scar carries a story, and every tear waters something new.
You’re not behind. You’re not broken.
You’re becoming.
So breathe. Pause.
And trust that this chapter is shaping a version of you that’s stronger than ever before.""",

    "inspiration": """You weren’t made to blend in—you were born to shine.
The dream inside you exists for a reason.
Even if the path is foggy, take that step.
Even if no one claps, keep creating.
Because one act of bravery can ignite a lifetime of purpose.
You have a voice. A vision. A light the world hasn’t seen yet.
Keep going.
Keep dreaming.
You’re closer than you think, and your story is just beginning.
Let the world feel your spark.""",

    "sad": """Some days just hurt more than others.
You smile in front of everyone, but your heart aches in silence.
You wonder if anyone notices.
You replay memories. You miss people who left.
You carry pain no one sees.
But even in the quiet, healing happens.
Even when you feel lost, you’re still moving forward.
It’s okay to feel tired. It’s okay to cry.
But don’t give up.
There’s light beyond this tunnel.
Brighter days are coming—hold on just a little longer."""
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

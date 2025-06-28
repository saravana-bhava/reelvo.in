# utils/generate_script.py

import os
from dotenv import load_dotenv
import openai
from openai import OpenAIError, RateLimitError
from textwrap import dedent

# Load .env
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

# Optional: progress hook
try:
    from progress import update_progress
except ImportError:
    def update_progress(task_id, status, percent):
        pass

FALLBACKS = {
    "motivation": """Every champion started as a beginner who refused to quit.
You don’t need the full map—just the courage to begin.
You’ll fall. You’ll doubt yourself. But you’ll rise again.
Growth doesn’t come from comfort—it comes from courage.
It comes from showing up when it’s hard, not when it’s easy.
Even on slow days, keep going. You’ve got this.
The path is hard, but the progress is real.
One day, you’ll thank yourself—for not quitting when it was hardest to stay.""",

    "success": """People only see the win—they don’t see what it cost.
They don’t see the sleepless nights, the setbacks, the silent tears.
They don’t hear the voice that said, “Quit,” and the one that whispered, “Keep going.”
Success isn’t applause—it’s persistence when no one’s clapping.
It’s getting back up—again and again—without validation.
This victory? It’s built on effort, sacrifice, and belief.
It’s yours because you earned it. You kept showing up.
That’s what success really looks like.""",

    "life": """Life doesn’t always go as planned.
It breaks you, reshapes you, and teaches you to rebuild.
You laugh with others, then cry alone—wondering if you matter.
But every tear waters strength. Every scar is proof you’re healing.
You’re not behind—you’re in bloom.
Progress isn’t always loud. Becoming takes time.
You’re not lost—you’re growing.
Breathe. Trust this season.
This chapter is not the end. It’s your becoming.""",

    "inspiration": """You weren’t born to blend in—you were made to stand out.
That dream in your heart exists for a reason.
Even if no one believes in it yet—start anyway.
Keep building. Keep creating. Someone out there needs your light.
You’re not too small. You’re not too late.
You are capable, you are worthy, and you are needed.
Speak your truth. Share your gift.
The story you carry—it’s just getting started.""",

    "sad": """Some days just hurt more than others.
You smile for the world, but ache in silence.
You miss what was. You wonder what could’ve been.
And that’s okay. You’re allowed to feel this deeply.
Even in pain, your heart is healing.
You are not weak—you are human.
You’re still here. Still breathing. Still trying.
And that is enough.
Don’t give up. You’re closer than you think to the light.""",
}


def generate_script(theme: str, task_id=None) -> str:
    theme = theme.lower()
    update_progress(task_id, "🧠 Generating script...", 10)

    if not USE_OPENAI:
        print(f"⚠️ OpenAI disabled. Using fallback for '{theme}'")
        update_progress(task_id, "📝 Using fallback script", 12)
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
        update_progress(task_id, "✅ Script generated", 15)
        return script

    except RateLimitError:
        print("⚠️ OpenAI rate limit hit. Using fallback.")
    except OpenAIError as e:
        print(f"[❌] OpenAI error: {e}")
    except Exception as e:
        print(f"[❌] Unexpected error: {e}")

    update_progress(task_id, "⚠️ Using fallback script", 12)
    return FALLBACKS.get(theme, f"This is a fallback script for the theme '{theme}'.")


def generate_script_for_user(theme: str, username: str, output_root: str = "output", task_id=None) -> str:
    output_dir = os.path.join(output_root, username)
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, f"{theme}_text.txt")
    if os.path.exists(output_path):
        print(f"[📝] Script already exists → {output_path}")
        return output_path

    script = generate_script(theme, task_id)
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

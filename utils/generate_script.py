# utils/generate_script.py

"""
Generates short Instagram reel scripts using OpenAI or category-specific fallbacks.
Saves output to: output/{username}/{theme}_text.txt
Supports: English / Hindi script generation
"""

import os
from textwrap import dedent
from dotenv import load_dotenv
import openai
from openai import OpenAIError, RateLimitError

# Load environment
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

# Optional progress hook
try:
    from progress import update_progress
except ImportError:
    def update_progress(task_id, status, percent): pass

# Fallback scripts (English & Hindi only for now)
FALLBACKS = {
    "motivation": {
        "en": """Every champion started as a beginner who refused to quit.
You don’t need the full map—just the courage to begin.
You’ll fall. You’ll doubt yourself. But you’ll rise again.
Growth doesn’t come from comfort—it comes from courage.
The path is hard, but the progress is real.""",
        "hi": """हर चैंपियन कभी एक ऐसा शुरुआतकर्ता था जिसने हार मानने से इनकार कर दिया।
आपको पूरी योजना नहीं चाहिए—सिर्फ शुरुआत करने का साहस चाहिए।
आप गिरोगे, खुद पर संदेह होगा, लेकिन आप फिर उठोगे।
विकास हमेशा आराम से नहीं आता—वो साहस से आता है।
रास्ता कठिन है, लेकिन प्रगति असली है।"""
    },
    "sad": {
        "en": """Some days just hurt more than others.
You smile for the world, but ache in silence.
Even in pain, your heart is healing.
You are not weak—you are human.""",
        "hi": """कुछ दिन दूसरों से ज़्यादा तकलीफ देते हैं।
दुनिया के लिए मुस्कुराते हो, लेकिन अंदर से टूटे हो।
इस दर्द में भी, दिल धीरे-धीरे ठीक हो रहा है।
आप कमजोर नहीं—इंसान हो।"""
    },
    "PostureFix Pro": {
        "hi": """पीठ झुका ली ना फिर से?
सारा दिन कंप्यूटर, मोबाइल… और फिर वही कमर दर्द! 😩
अब लाओ PostureFix Pro™!
✅ हल्का, पहनने में आसान
👇 नीचे क्लिक करो — अपनी रीढ़ की हड्डी को आज ही राहत दो!"""
    }
}


def generate_script(theme: str, task_id=None, language="en") -> str:
    """Generate a 30-sec script in desired language."""
    theme = theme.lower()
    language = language.lower()
    update_progress(task_id, "🧠 Generating script...", 10)

    if not USE_OPENAI:
        print(f"⚠️ OpenAI disabled. Using fallback for '{theme}' in '{language}'")
        update_progress(task_id, "📝 Using fallback script", 12)
        return FALLBACKS.get(theme, {}).get(language, f"Fallback script for '{theme}' in {language}")

    lang_prompt = {
        "en": "in English",
        "hi": "in Hindi"
    }.get(language, "in English")

    prompt = (
        f"Write a short, powerful Instagram reel script on the theme: '{theme}', {lang_prompt}. "
        f"Use 4–5 short impactful lines. Keep it under 30 seconds for voiceover."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{ "role": "user", "content": prompt }],
            temperature=0.7
        )
        script = response.choices[0].message.content.strip()
        print(f"[✅] OpenAI script generated for '{theme}' in '{language}'")
        update_progress(task_id, "✅ Script generated", 15)
        return script

    except RateLimitError:
        print("⚠️ OpenAI rate limit hit. Using fallback.")
    except OpenAIError as e:
        print(f"[❌] OpenAI error: {e}")
    except Exception as e:
        print(f"[❌] Unexpected error: {e}")

    update_progress(task_id, "⚠️ Using fallback script", 12)
    return FALLBACKS.get(theme, {}).get(language, f"Fallback script for '{theme}' in {language}")


def generate_script_for_user(theme: str, username: str, output_root: str = "output", task_id=None, language="en") -> str:
    """Generate and save a script for a user and theme in given language."""
    output_dir = os.path.join(output_root, username)
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, f"{theme}_text.txt")
    if os.path.exists(output_path):
        print(f"[📝] Script already exists → {output_path}")
        return output_path

    script = generate_script(theme, task_id, language=language)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(dedent(script).strip())

    print(f"[📄] Script saved → {output_path}")
    return output_path


# CLI
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python utils/generate_script.py <theme> <username> [language=en]")
    else:
        theme, username = sys.argv[1], sys.argv[2]
        lang = sys.argv[3] if len(sys.argv) == 4 else "en"
        generate_script_for_user(theme, username, language=lang)

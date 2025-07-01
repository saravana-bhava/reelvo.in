# File: utils/generate_script.py

"""
Generates short Instagram reel scripts using OpenAI or fallback.
Saves output to: output/{username}/{theme}_{lang}_text.txt
Supports: English and Hindi
"""

import os
import json
import logging
from textwrap import dedent
from dotenv import load_dotenv
from typing import Optional
import openai
from openai import OpenAIError, RateLimitError

# Setup
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(ROOT_DIR, ".env"))

logger = logging.getLogger("script_gen")
logging.basicConfig(level=logging.INFO)

# Constants
USE_OPENAI = os.getenv("USE_OPENAI", "true").lower() == "true"
API_KEY = os.getenv("OPENAI_API_KEY")
FALLBACK_JSON_PATH = os.path.join(ROOT_DIR, "fallback_scripts.json")

# Load fallback scripts
try:
    with open(FALLBACK_JSON_PATH, "r", encoding="utf-8") as f:
        FALLBACKS = json.load(f)
    logger.info("[🗂️] Fallback scripts loaded.")
except FileNotFoundError:
    logger.warning("[⚠️] Fallback scripts file not found.")
    FALLBACKS = {}

# Initialize OpenAI client
if USE_OPENAI:
    if not API_KEY:
        raise EnvironmentError("[❌] Missing OPENAI_API_KEY in .env")
    client = openai.OpenAI(api_key=API_KEY)
else:
    client = None

# Optional progress UI support
try:
    from progress import update_progress
except ImportError:
    def update_progress(task_id, status, percent): pass

# Custom prompt overrides
PROMPT_TEMPLATES = {
    "posturefix pro": {
        "hi": "Write a catchy, 20–30s Hindi Instagram ad script for PostureFix Pro, a smart posture corrector. Focus on pain relief, alert feature, and emotional appeal. Use emojis and clear CTAs."
    }
}


def generate_script(theme: str, task_id: Optional[str] = None, language: str = "en") -> str:
    """
    Generate a 30-second Instagram script using OpenAI or fallback.

    Args:
        theme (str): Script category (e.g., "motivation").
        task_id (str): Optional task ID for UI updates.
        language (str): "en" or "hi".

    Returns:
        str: Script text.
    """
    theme_norm = theme.strip().lower()
    language_norm = language.strip().lower()

    update_progress(task_id, "🧠 Generating script...", 10)

    def fallback_script() -> str:
        return FALLBACKS.get(theme_norm, {}).get(language_norm, f"[Fallback script for '{theme_norm}' in '{language_norm}']")

    # Use predefined prompt template if available
    if theme_norm in PROMPT_TEMPLATES and language_norm in PROMPT_TEMPLATES[theme_norm]:
        prompt = PROMPT_TEMPLATES[theme_norm][language_norm]
    else:
        prompt = (
            f"Write a short, impactful Instagram reel script about '{theme}' "
            f"{'in Hindi' if language_norm == 'hi' else 'in English'}. "
            "Keep it under 30 seconds, using 4–5 emotional and punchy lines for voiceover."
        )

    if USE_OPENAI and client:
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            script = response.choices[0].message.content.strip()
            logger.info(f"[✅] OpenAI script generated for '{theme}' ({language})")
            update_progress(task_id, "✅ Script generated", 15)
            return script
        except RateLimitError:
            logger.warning("⚠️ OpenAI rate limit hit. Using fallback.")
        except OpenAIError as e:
            logger.error(f"[❌] OpenAI error: {e}")
        except Exception as e:
            logger.error(f"[❌] Unexpected error: {e}")

    # Fallback
    update_progress(task_id, "⚠️ Using fallback script", 12)
    logger.info(f"[⚠️] Using fallback script for '{theme}' in '{language}'")
    return fallback_script()


def generate_script_for_user(
    theme: str,
    username: str,
    language: str = "en",
    output_root: str = "output",
    task_id: Optional[str] = None
) -> str:
    """
    Generate and save a script for a user under: output/{username}/

    Returns:
        str: Full path to saved script file.
    """
    output_dir = os.path.join(output_root, username)
    os.makedirs(output_dir, exist_ok=True)

    lang_suffix = "_hi" if language == "hi" else "_en"
    output_path = os.path.join(output_dir, f"{theme}{lang_suffix}_text.txt")

    if os.path.exists(output_path):
        logger.info(f"[📝] Script already exists → {output_path}")
        return output_path

    script = generate_script(theme, task_id, language=language)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(dedent(script).strip())

    logger.info(f"[📄] Script saved → {output_path}")
    return output_path


# CLI support
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python utils/generate_script.py <theme> <username> [language=en]")
    else:
        theme = sys.argv[1]
        username = sys.argv[2]
        language = sys.argv[3] if len(sys.argv) > 3 else "en"
        path = generate_script_for_user(theme, username, language)
        print(f"✅ Saved: {path}")

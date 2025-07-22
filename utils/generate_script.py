# File: utils/generate_script.py

"""
Generates short Instagram reel scripts using OpenAI or fallback from DB.
Saves output to: output/{user_email}/scripts/{theme_name}_{language}_text.txt
Supports: English and Hindi
"""

import os
import logging
from textwrap import dedent
from dotenv import load_dotenv
from typing import Optional
import httpx

# Setup
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(ROOT_DIR, ".env"))

logger = logging.getLogger("script_gen")
logging.basicConfig(level=logging.INFO)

# Constants
USE_OPENAI = os.getenv("USE_OPENAI", "true").lower() == "true"
PROVIDER = os.getenv("PROVIDER", "openai").lower()
API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

# Optional progress UI support
try:
    from progress import update_progress
except ImportError:
    def update_progress(task_id, status, percent): pass


def generate_script_via_api(prompt: str) -> Optional[str]:
    """Generates a script using OpenAI-compatible API."""
    if not API_KEY:
        logger.error("[🔑] No API key provided for OpenAI/OpenRouter.")
        return None

    try:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }

        if PROVIDER == "openrouter":
            headers["HTTP-Referer"] = "https://yourdomain.com/"
            headers["X-Title"] = "Reel Script Generator"

        url = f"{BASE_URL.rstrip('/')}/chat/completions"

        payload = {
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }

        logger.info(f"[📡] Sending request to {url} via {PROVIDER}...")
        response = httpx.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()

        response_data = response.json()
        if "choices" not in response_data or not response_data["choices"]:
            logger.error("[❌] No choices returned in response.")
            return None

        script = response_data["choices"][0]["message"]["content"].strip()

        # Strip quotes if wrapped
        if (script.startswith('"') and script.endswith('"')) or (script.startswith("“") and script.endswith("”")):
            script = script[1:-1].strip()

        return script

    except httpx.HTTPStatusError as e:
        logger.error(f"[❌] HTTP error during API call: {e}")
    except Exception as e:
        logger.error(f"[❌] Unexpected error during script generation: {e}")
    return None


def generate_script(prompt: str, language: str = "en") -> str:
    """
    Generate a 30-second Instagram script using OpenAI or DB fallback.
    """
    prompt_norm = prompt.strip().lower()
    language_norm = language.strip().lower()

    def fallback_script() -> str:
        from models.theme import Theme
        theme = Theme.query.filter_by(name=prompt_norm, lang=language_norm).first()
        if theme:
            return dedent(theme.content).strip()
        else:
            available = Theme.query.filter_by(name=prompt_norm).all()
            langs = list(set(t.lang for t in available))
            logger.warning(f"[⚠️] No fallback for '{prompt_norm}' in '{language_norm}'. Available: {langs}")
            return f"[Theme script for '{prompt_norm}' in '{language_norm}']"

    chat_prompt = (
        f"Write a short voiceover script for an Instagram Reel. "
        f"The theme is '{prompt_norm}', "
        f"language: {'Hindi' if language_norm == 'hi' else 'English'}. "
        f"The script should be under 30 seconds, energetic, emotional, and impactful. "
        f"Output only the script lines—no headings, emojis, scene directions, or bullet points."
    )

    if USE_OPENAI:
        script = generate_script_via_api(chat_prompt)
        if script:
            logger.info(f"[✅] Script generated for '{prompt}' ({language})")
            return script

    logger.info(f"[⚠️] Using fallback script for '{prompt}' ({language})")
    return fallback_script()


def generate_script_for_user(
    user_email: str,
    folder_name: str,
    theme_name: str,
    language: str = "en",
    prompt: str = ""
) -> str:
    """
    Wrapper to generate and store a script for a user.
    """
    logger.info(f"[📝] Generating script → User: '{user_email}', Folder: '{folder_name}', Theme: '{theme_name}', Language: '{language}', Prompt: '{prompt}'")

    update_progress(folder_name, "generating_script", 25)

    output_dir = os.path.join("output", user_email, folder_name)
    os.makedirs(output_dir, exist_ok=True)

    script_path = os.path.join(output_dir, f"{theme_name}_{language}_text.txt")

    script = generate_script(prompt=prompt, language=language)
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(dedent(script).strip())

    update_progress(folder_name, "script_generated", 30)
    logger.info(f"[📄] Script saved → {script_path}")
    return script_path


# CLI support
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 6:
        print("Usage: python utils/generate_script.py <user_email> <folder_name> <theme_name> <language> <prompt>")
        sys.exit(1)

    user_email = sys.argv[1]
    folder_name = sys.argv[2]
    theme_name = sys.argv[3]
    language = sys.argv[4]
    prompt = sys.argv[5]

    result_path = generate_script_for_user(
        user_email=user_email,
        folder_name=folder_name,
        theme_name=theme_name,
        language=language,
        prompt=prompt
    )

    print(f"✅ Saved: {result_path}")

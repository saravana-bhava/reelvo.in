# File: utils/generate_script.py

"""
Generates short Instagram reel scripts using OpenAI or fallback.
Saves output to: output/scripts/{username}/{theme}_{lang}_text.txt
Supports: English and Hindi
"""

import os
import json
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
THEME_JSON_PATH = os.path.join(ROOT_DIR, "theme.json")

# Load fallback theme scripts
try:
    with open(THEME_JSON_PATH, "r", encoding="utf-8") as f:
        THEMES = json.load(f)
    logger.info("[🗂️] Theme scripts loaded.")
except FileNotFoundError:
    logger.warning("[⚠️] Theme scripts file not found.")
    THEMES = {}

# Optional progress UI support
try:
    from progress import update_progress
except ImportError:
    def update_progress(task_id, status, percent): pass


def generate_script_via_api(prompt: str) -> Optional[str]:
    """
    Generates text using OpenAI-compatible APIs (OpenAI or OpenRouter).
    Returns None if generation fails.
    """
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

        try:
            response_data = response.json()
            script = response_data["choices"][0]["message"]["content"].strip()
            # Remove leading/trailing quotes if present
            if script.startswith('"') and script.endswith('"'):
                script = script[1:-1].strip()
            elif script.startswith("“") and script.endswith("”"):
                script = script[1:-1].strip()
            return script
        except json.JSONDecodeError:
            logger.error(f"[❌] Failed to decode JSON. Raw response: {response.text}")
        except KeyError as e:
            logger.error(f"[❌] Missing expected field {e} in response: {response.text}")

    except httpx.HTTPStatusError as e:
        logger.error(f"[❌] Error generating via API: {e}")
    except Exception as e:
        logger.error(f"[❌] Unexpected error during script generation: {e}")

    return None


def generate_script(theme: str, task_id: Optional[str] = None, language: str = "en") -> str:
    """
    Generate a 30-second Instagram script using OpenAI or fallback.
    """
    theme_norm = theme.strip().lower()
    language_norm = language.strip().lower()

    update_progress(task_id, "🧠 Generating script...", 10)

    def fallback_script() -> str:
        return THEMES.get(theme_norm, {}).get(language_norm, f"[Theme script for '{theme_norm}' in '{language_norm}']")

    prompt = (
        f"Write only the voiceover lines (no scene descriptions, no headers, no visuals, no call-to-action). "
        f"The topic is '{theme}', "
        f"{'in Hindi' if language_norm == 'hi' else 'in English'}. "
        "Make it under 30 seconds, and keep it emotional, energetic, and impactful. "
        "Do not include any headings, bullet points, emojis, or visual cues — just the plain script lines."
    )

    if USE_OPENAI:
        script = generate_script_via_api(prompt)
        if script:
            logger.info(f"[✅] Script generated for '{theme}' ({language})")
            update_progress(task_id, "✅ Script generated", 15)
            return script

    # Fallback
    logger.info(f"[⚠️] Using fallback script for '{theme}' ({language})")
    update_progress(task_id, "⚠️ Using theme script", 12)
    return fallback_script()


def generate_script_for_user(
    theme: str,
    username: str,
    language: str = "en",
    output_root: str = "output/scripts",
    task_id: Optional[str] = None
) -> str:
    """
    Generate and save a script for a user under: output/scripts/{username}/
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

# File: utils/generate_script.py

"""
Generates short Instagram reel scripts using OpenAI or fallback.
Saves output to: output/{user_name}/scripts/{theme_name}_{language}_text.txt
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

        response_data = response.json()
        if "choices" not in response_data or not response_data["choices"]:
            logger.error("[❌] No choices returned in response.")
            return None

        script = response_data["choices"][0]["message"]["content"].strip()
        # Remove leading/trailing quotes if present
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
    Generate a 30-second Instagram script using OpenAI or fallback.
    """
    prompt_norm = prompt.strip().lower()
    language_norm = language.strip().lower()

    def fallback_script() -> str:
        return THEMES.get(prompt_norm, {}).get(language_norm, f"[Theme script for '{prompt_norm}' in '{language_norm}']")

    chat_prompt = (
        f"Write only the voiceover lines (no scene descriptions, no headers, no visuals, no call-to-action). "
        f"The topic is '{prompt_norm}', "
        f"{'in Hindi' if language_norm == 'hi' else 'in English'}. "
        "Make it under 30 seconds, and keep it emotional, energetic, and impactful. "
        "Do not include any headings, bullet points, emojis, or visual cues — just the plain script lines."
    )

    if USE_OPENAI:
        script = generate_script_via_api(chat_prompt)
        if script:
            logger.info(f"[✅] Script generated for '{prompt}' ({language})")
            return script

    # Fallback
    logger.info(f"[⚠️] Using fallback script for '{prompt}' ({language})")
    return fallback_script()


def generate_script_for_user(
    user_name: str,
    folder_name: str,
    theme_name: str,
    language: str = "en",
    prompt: str = ""
) -> str:
    """
    Wrapper to generate and store script for a user.
    """
    logger.info(f"[📝] Generating script for User: '{user_name}', Folder: '{folder_name}', Theme: '{theme_name}', Language: '{language}', Prompt: '{prompt}'")

    output_dir = os.path.join("output", user_name, folder_name)
    os.makedirs(output_dir, exist_ok=True)

    script_path = os.path.join(output_dir, f"{theme_name}_{language}_text.txt")

    if os.path.exists(script_path):
        logger.info(f"[📝] Script already exists → {script_path}")
        return script_path

    script = generate_script(prompt=prompt, language=language)
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(dedent(script).strip())

    logger.info(f"[📄] Script saved → {script_path}")
    return script_path


# CLI support
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 6:
        print("Usage: python utils/generate_script.py <user_name> <folder_name> <theme_name> <language> <prompt>")
        sys.exit(1)

    user_name = sys.argv[1]
    folder_name = sys.argv[2]
    theme_name = sys.argv[3]
    language = sys.argv[4]
    prompt = sys.argv[5]

    script_path = generate_script_for_user(
        user_name=user_name,
        folder_name=folder_name,
        theme_name=theme_name,
        language=language,
        prompt=prompt
    )
    print(f"✅ Saved: {script_path}")

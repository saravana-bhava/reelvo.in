# ================================================
# File:         utils/generate_script.py
# Description:  Generate reel captions/script via AI
# Framework:    Flask + TailwindCSS
# Version:      1.0.0
# Last Updated: 12 August 2025
# Author:       Saravana Bhava
# Author URL:   https://SazM.in
# ================================================

"""
Generates short Instagram reel scripts using OpenAI.
Saves output to: output/{user_email}/scripts/{theme_name}_{language}_text.txt
Supports: English and Hindi
"""

import os
import logging
from textwrap import dedent
from dotenv import load_dotenv
from typing import Optional
import httpx
import sys
import uuid

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


def clean_script_text(script: str) -> str:
    """Normalize script output by removing unwanted wrappers or labels."""
    text = script.strip()

    # Strip quotes if wrapped
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("“") and text.endswith("”")):
        text = text[1:-1].strip()

    # Remove leading "Script:", "Voiceover:", etc.
    for prefix in ["script:", "voiceover:", "narration:", "caption:"]:
        if text.lower().startswith(prefix):
            text = text[len(prefix):].strip()
            break

    return text


def generate_script_via_api(prompt: str) -> Optional[str]:
    """Generates a script using OpenAI-compatible API."""
    if not API_KEY:
        logger.error("[🔑] No API key provided for OpenAI/OpenRouter.")
        return None

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

    try:
        logger.info(f"[📡] Sending request to {url} via {PROVIDER}...")
        response = httpx.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()

        response_data = response.json()
        if not response_data.get("choices"):
            logger.error("[❌] No choices returned in response.")
            return None

        raw_script = response_data["choices"][0]["message"]["content"]
        script = clean_script_text(raw_script)
        return script
    except httpx.HTTPStatusError as e:
        logger.error(f"[❌] HTTP error during API call: {e}")
    except httpx.RequestError as e:
        logger.error(f"[❌] Request error during API call: {e}")
    except Exception as e:
        logger.error(f"[❌] Unexpected error during script generation: {e}")
    return None


def fallback_script(prompt_norm: str, language_norm: str) -> str:
    """Return a static fallback if API fails."""
    logger.warning(f"[⚠️] No API response, using static fallback for '{prompt_norm}' ({language_norm})")
    return f"[Default script for '{prompt_norm}' in '{language_norm}']"


def generate_script(prompt: str, language: str = "en") -> str:
    """
    Generate a 30-second Instagram script using OpenAI or static fallback.
    Guarantees a non-empty script.
    """
    prompt_norm = prompt.strip().lower()
    language_norm = language.strip().lower()

    variation_seed = str(uuid.uuid4())[:8]

    chat_prompt = (
        f"Write a short, original voiceover script for an Instagram Reel. "
        f"The theme is '{prompt_norm}', "
        f"language: {'Hindi' if language_norm == 'hi' else 'English'}. "
        f"The script should be under 30 seconds, energetic, emotional, and impactful. "
        f"Output only the script text itself — do not include any labels like 'Script:', 'Voiceover:', 'Narration:', or similar. "
        f"Add subtle variation. Seed: {variation_seed}"
    )

    if USE_OPENAI:
        script = generate_script_via_api(chat_prompt)
        if script:
            logger.info(f"[✅] Script generated for '{prompt}' ({language})")
            return script
        else:
            logger.warning(f"[⚠️] API failed, falling back for '{prompt}' ({language})")

    return fallback_script(prompt_norm, language_norm)


def generate_script_for_user(
    user_email: str,
    folder_name: str,
    theme_name: str,
    language: str = "en",
    prompt: str = ""
) -> Optional[str]:
    """
    Wrapper to generate and store a script for a user.
    Ensures a script file is always written if possible.
    """
    logger.info(
        f"[📝] Generating script → User: '{user_email}', Folder: '{folder_name}', "
        f"Theme: '{theme_name}', Language: '{language}', Prompt: '{prompt}'"
    )

    update_progress(folder_name, "generating_script", 25)

    output_dir = os.path.join("output", user_email, folder_name)
    os.makedirs(output_dir, exist_ok=True)

    script_path = os.path.join(output_dir, f"{theme_name}_{language}_text.txt")

    script = generate_script(prompt=prompt, language=language)
    if not script or not script.strip():
        logger.error(f"[❌] Script generation failed for '{theme_name}' — no file created.")
        return None

    try:
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(dedent(script).strip())
    except Exception as e:
        logger.error(f"[❌] Error writing script to file: {e}")
        return None

    # Verify file exists and not empty
    if not os.path.exists(script_path) or os.path.getsize(script_path) == 0:
        logger.error(f"[❌] Failed to save script → {script_path}")
        return None

    update_progress(folder_name, "script_generated", 30)
    logger.info(f"[📄] Script saved → {script_path}")
    return script_path


# CLI support
if __name__ == "__main__":
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

    if result_path:
        print(f"✅ Saved: {result_path}")
    else:
        print("❌ Script generation failed.")

# ================================================
# File:         utils/translate_text.py
# Description:  Translate text via external API
# Framework:    Flask + TailwindCSS
# Version:      1.0.0
# Last Updated: 31 July 2025
# Author:       Saravana Bhava
# Author URL:   https://SazM.in
# ================================================

"""
Translate input text to English using Deep Translator (Google Translate backend).
Falls back to original text if translation fails.
"""

import logging
from deep_translator import GoogleTranslator

# Logger setup (configured only if no handlers exist)
logger = logging.getLogger("translator")
if not logger.hasHandlers():
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s:%(name)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def translate_to_english(text: str) -> str:
    """
    Translates text from any language to English using Deep Translator (Google Translate backend).
    Returns the original text if translation fails.

    Args:
        text (str): Input text in any language.

    Returns:
        str: Translated text in English, or original text on failure.
    """
    if not text or not isinstance(text, str):
        logger.warning("[⚠️] Invalid input for translation.")
        return text

    try:
        translated = GoogleTranslator(source="auto", target="en").translate(text)
        if translated:
            return translated.strip()
        else:
            logger.warning("[⚠️] Received empty translation.")
            return text
    except Exception as e:
        logger.warning(f"[⚠️] Translation failed: {e}")
        return text


# CLI for terminal testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python utils/translate_text.py '<text>'")
        sys.exit(1)

    input_text = " ".join(sys.argv[1:])
    result = translate_to_english(input_text)
    print(f"🔁 Translated:\n{result}")

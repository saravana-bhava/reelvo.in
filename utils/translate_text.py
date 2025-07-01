# File: utils/translate_text.py

"""
Translate input text to English using Deep Translator (Google Translate backend).
Falls back to original text if translation fails.
"""

import logging
from deep_translator import GoogleTranslator

# Logger setup
logger = logging.getLogger("translator")
logging.basicConfig(level=logging.INFO)


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
    else:
        input_text = " ".join(sys.argv[1:])
        translated = translate_to_english(input_text)
        print(f"🔁 Translated: {translated}")

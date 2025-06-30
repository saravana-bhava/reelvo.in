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
    Translate text from any language to English using Google Translate API via deep_translator.

    Args:
        text (str): Input text in any language.

    Returns:
        str: Translated text in English, or original if translation fails.
    """
    try:
        return GoogleTranslator(source="auto", target="en").translate(text)
    except Exception as e:
        logger.warning(f"[⚠️] Translation failed: {e}")
        return text


# CLI for testing translation from terminal
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python utils/translate_text.py '<text>'")
    else:
        input_text = sys.argv[1]
        translated = translate_to_english(input_text)
        print(f"🔁 Translated: {translated}")

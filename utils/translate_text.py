# File: utils/translate_text.py

"""
Translate input text to English using Deep Translator (Google Translate backend).
Falls back to original text if translation fails.
"""

from deep_translator import GoogleTranslator

def translate_to_english(text: str) -> str:
    """Translate any language to English using DeepTranslator."""
    try:
        translated = GoogleTranslator(source='auto', target='en').translate(text)
        return translated
    except Exception as e:
        print(f"[⚠️] Translation failed: {e}")
        return text


# CLI for testing
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python utils/translate_text.py '<text>'")
    else:
        input_text = sys.argv[1]
        print(translate_to_english(input_text))


import openai
import os
from dotenv import load_dotenv
from openai import OpenAIError, RateLimitError

load_dotenv()

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

fallbacks = {
    "motivation": "Keep going! Your hard work will pay off soon. This is your moment.",
    "sad": "It's okay to feel down sometimes. Just remember, brighter days are ahead.",
    "inspiration": "The best view comes after the hardest climb. Keep moving forward.",
    "success": "Success doesn't come from what you do occasionally, it comes from what you do consistently.",
    "life": "Life is a journey filled with highs and lows—embrace every moment."
}

def generate_script(theme):
    prompt = f"Write a short, powerful Instagram reel script about the theme: {theme}."

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{ "role": "user", "content": prompt }],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()

    except RateLimitError:
        print("⚠️ OpenAI Rate Limit: Using fallback script.")
        return fallbacks.get(theme.lower(), f"This is a fallback script for the theme '{theme}'.")

    except OpenAIError as e:
        print(f"❌ OpenAI API Error: {str(e)}")
        return fallbacks.get(theme.lower(), f"OpenAI error occurred. Here's a generic fallback script for '{theme}'.")

    except Exception as e:
        print(f"❌ Unknown error: {e}")
        return "Something went wrong while generating the script."

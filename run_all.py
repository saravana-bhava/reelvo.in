# run_all.py

from run_pipeline import run_pipeline
import time

CATEGORIES = ["motivation", "success", "life", "inspiration", "sad"]

def main():
    print("🚀 Starting full batch reel generation...\n")

    for category in CATEGORIES:
        print(f"🔹 Processing: {category}")
        try:
            run_pipeline(category)
        except Exception as e:
            print(f"[❌] Error processing '{category}': {e}")
        time.sleep(3)  # Small delay to avoid API rate limits

    print("\n✅ All reels generated successfully.")

if __name__ == "__main__":
    main()

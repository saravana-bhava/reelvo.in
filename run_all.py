# run_all.py

from run_pipeline import run_pipeline
import time

CATEGORIES = ["motivation", "success", "life", "inspiration", "sad"]
USERNAME = "demo"  # 👈 Change this as needed

def main():
    print(f"🚀 Starting full batch reel generation for user: {USERNAME}\n")

    for category in CATEGORIES:
        print(f"🔹 Processing: {category}")
        try:
            run_pipeline(category, USERNAME)
        except Exception as e:
            print(f"[❌] Error processing '{category}': {e}")
        time.sleep(2)  # Delay to avoid rate limits or API congestion

    print(f"\n✅ All reels generated successfully for user: {USERNAME}")

if __name__ == "__main__":
    main()

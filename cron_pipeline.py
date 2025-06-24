# cron_pipeline.py

import time
from run_pipeline import run_pipeline

CATEGORIES = ["motivation", "success", "life", "inspiration", "sad"]

def run_all_categories():
    for category in CATEGORIES:
        try:
            print(f"\n🕒 [CRON] Starting reel generation for: {category}")
            run_pipeline(category)
            time.sleep(5)  # Prevent rate-limiting
        except Exception as e:
            print(f"[❌] Failed for category '{category}': {e}")

if __name__ == "__main__":
    print("🌀 Running cron-based reel generation for all categories...")
    run_all_categories()
    print("\n✅ Cron job finished.")

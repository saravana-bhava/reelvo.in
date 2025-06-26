# cron_pipeline.py

import time
from run_pipeline import run_pipeline

CATEGORIES = ["motivation", "success", "life", "inspiration", "sad"]
USERNAME = "demo"  # 👈 Update this to your target username

def run_all_categories_for_user(username):
    for category in CATEGORIES:
        try:
            print(f"\n🕒 [CRON] Starting reel generation for: {category} | User: {username}")
            run_pipeline(category, username)
            time.sleep(5)  # Prevent API rate-limiting
        except Exception as e:
            print(f"[❌] Failed for category '{category}': {e}")

if __name__ == "__main__":
    print(f"🌀 Running cron-based reel generation for user: {USERNAME}")
    run_all_categories_for_user(USERNAME)
    print("\n✅ Cron job finished.")

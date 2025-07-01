from datetime import datetime
import os
import json
from utils.instagram_upload import post_reel
from utils.user_db import get_user_token

SCHEDULE_DIR = "reels_metadata"

def run_scheduler():
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    current_hour = now.strftime("%H:%M")

    for user_file in os.listdir(SCHEDULE_DIR):
        username = user_file.replace(".json", "")
        user_path = os.path.join(SCHEDULE_DIR, user_file)

        with open(user_path) as f:
            reels = json.load(f)

        updated = False
        for reel in reels:
            if reel["status"] == "scheduled" and reel["scheduled_date"] == today and reel["scheduled_time"] == "16:00":
                token_info = get_user_token(username)
                if token_info:
                    try:
                        post_reel(token_info, reel["video_path"], reel["caption"])
                        reel["status"] = "posted"
                        reel["posted_at"] = now.isoformat()
                        updated = True
                        print(f"[{username}] ✅ Posted reel: {reel['video_path']}")
                    except Exception as e:
                        print(f"[{username}] ❌ Failed to post reel: {e}")
                        # Optionally: mark as "failed"
        if updated:
            with open(user_path, "w") as f:
                json.dump(reels, f, indent=2)

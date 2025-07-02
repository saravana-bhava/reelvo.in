# File: scheduler/post_scheduled_reels.py

from datetime import datetime
import os
import json
from utils.instagram_upload import post_reel
from utils.user_db import get_user_token

SCHEDULE_DIR = "reels_metadata"
SCHEDULED_HOUR = "16:00"


def run_scheduler():
    """
    Checks for reels scheduled to be posted at the current date/time,
    and posts them to Instagram via Graph API.
    """
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")

    for user_file in os.listdir(SCHEDULE_DIR):
        if not user_file.endswith(".json"):
            continue

        username = user_file.replace(".json", "")
        user_path = os.path.join(SCHEDULE_DIR, user_file)

        try:
            with open(user_path, "r", encoding="utf-8") as f:
                reels = json.load(f)
        except Exception as e:
            print(f"[{username}] ❌ Failed to load schedule: {e}")
            continue

        updated = False

        for reel in reels:
            status = reel.get("status", "unknown")
            scheduled_date = reel.get("scheduled_date")
            scheduled_time = reel.get("scheduled_time")

            if (
                status == "scheduled"
                and scheduled_date == today
                and scheduled_time == SCHEDULED_HOUR
            ):
                token_info = get_user_token(username)
                if not token_info:
                    print(f"[{username}] ⚠️ Missing Instagram token. Skipping reel.")
                    continue

                try:
                    post_reel(
                        token_info=token_info,
                        video_path=reel["video_path"],
                        caption=reel.get("caption", "")
                    )
                    reel["status"] = "posted"
                    reel["posted_at"] = now.isoformat()
                    updated = True
                    print(f"[{username}] ✅ Posted reel: {reel['video_path']}")
                except Exception as e:
                    print(f"[{username}] ❌ Error posting reel: {e}")
                    # Optionally:
                    # reel["status"] = "failed"

        if updated:
            try:
                with open(user_path, "w", encoding="utf-8") as f:
                    json.dump(reels, f, indent=2, ensure_ascii=False)
                print(f"[{username}] 💾 Schedule file updated.")
            except Exception as e:
                print(f"[{username}] ❌ Failed to update schedule: {e}")


if __name__ == "__main__":
    run_scheduler()

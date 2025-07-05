# File: scheduler/publish_scheduled_reels.py

import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask
from utils.instagram import post_to_instagram
from utils.user_db import get_instagram_credentials
from utils.reel_history import add_reel_to_history
from routes.auth import send_email

# Load environment variables
load_dotenv()

# Setup logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/publish.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("scheduler")

# Load scheduled posts
SCHEDULE_PATH = "db/scheduled_posts.json"
DEFAULT_EMAIL = os.getenv("DEFAULT_EMAIL", "developer@sazm.in")


def load_scheduled():
    if os.path.exists(SCHEDULE_PATH):
        try:
            with open(SCHEDULE_PATH, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.error("❌ Failed to load scheduled_posts.json (invalid JSON)")
    return {}


def save_scheduled(data):
    os.makedirs(os.path.dirname(SCHEDULE_PATH), exist_ok=True)
    try:
        with open(SCHEDULE_PATH, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"❌ Failed to save updated schedule: {e}")


def send_notification(email, subject, body):
    app = Flask(__name__)
    app.config.update(
        SMTP_HOST=os.getenv("SMTP_HOST"),
        SMTP_PORT=int(os.getenv("SMTP_PORT", 587)),
        SMTP_USERNAME=os.getenv("SMTP_USERNAME"),
        SMTP_PASSWORD=os.getenv("SMTP_PASSWORD"),
        SMTP_SENDER_NAME=os.getenv("SMTP_SENDER_NAME", "Reelvo.ai"),
        SMTP_USE_TLS=os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    )
    with app.app_context():
        try:
            send_email(email, subject, body)
        except Exception as e:
            logger.error(f"❌ Failed to send email: {e}")


def post_due_reels():
    all_schedules = load_scheduled()
    updated = False
    now = datetime.now()

    for user, posts in all_schedules.items():
        for post in posts:
            if post.get("posted"):
                continue

            scheduled_for = post.get("scheduled_for")
            if not scheduled_for:
                continue

            try:
                scheduled_dt = datetime.fromisoformat(scheduled_for)
            except ValueError:
                logger.warning(f"⚠️ Invalid datetime format for user {user}: {scheduled_for}")
                continue

            if scheduled_dt > now:
                continue  # Not yet due

            video_path = os.path.join("output", user, "videos", post["video"])
            if not os.path.exists(video_path):
                logger.error(f"🚫 Video not found: {video_path}")
                continue

            caption = post.get("caption", "")
            video_url = ""  # Optionally use a generated public link

            try:
                html_result = post_to_instagram(
                    video_path=video_path,
                    caption=caption,
                    user_name=user,
                    video_url=video_url
                )
                post["posted"] = True
                add_reel_to_history(user, post["video"], caption)
                logger.info(f"✅ Posted: {post['video']} for {user}")
                send_notification(user, "🎉 Reel Posted Successfully", f"Your reel '{post['video']}' was posted at {now}.\n\n{html_result}")
                updated = True
            except Exception as e:
                logger.exception(f"❌ Failed to post reel for {user}: {e}")
                send_notification(user, "❌ Failed to Post Reel", f"An error occurred while posting your reel '{post['video']}':\n\n{e}")

    if updated:
        save_scheduled(all_schedules)


if __name__ == "__main__":
    try:
        post_due_reels()
    except Exception as e:
        logger.exception(f"💥 Fatal error in publish script: {e}")

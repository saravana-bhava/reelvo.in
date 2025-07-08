# File: scripts/post_scheduled_reels.py

"""
Posts reels scheduled for today using unified schedule (db/scheduled_posts.json).
Includes email alerting on failures and log rotation.
"""

import os
import json
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
from utils.instagram_posting import post_to_instagram
from utils.user_db import get_user_token_data

# Load .env
load_dotenv()

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
DB_DIR = os.path.join(ROOT_DIR, "db")
OUTPUT_DIR = os.path.join(ROOT_DIR, "output")
SCHEDULE_FILE = os.path.join(DB_DIR, "scheduled_posts.json")
HISTORY_FILE = os.path.join(DB_DIR, "reel_history.json")
LOG_FILE = os.path.join(BASE_DIR, "logs", "post_scheduled.log")
EMAIL_TEMPLATE = os.path.join(BASE_DIR, "templates", "email_alert_template.txt")

# Logging setup
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logger = logging.getLogger("scheduled_reels")
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(LOG_FILE, maxBytes=2 * 1024 * 1024, backupCount=3)
handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S"))
logger.addHandler(handler)

# Email alert
def send_email_alert(subject, message):
    try:
        with open(EMAIL_TEMPLATE, "r", encoding="utf-8") as f:
            body = f.read().format(log_path=LOG_FILE, error_message=message)

        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = os.getenv("SMTP_FROM_EMAIL", os.getenv("SMTP_USERNAME"))
        msg["To"] = os.getenv("ALERT_EMAIL", msg["From"])

        with smtplib.SMTP(os.getenv("SMTP_HOST"), int(os.getenv("SMTP_PORT", 587))) as server:
            if os.getenv("SMTP_USE_TLS", "true").lower() == "true":
                server.starttls()
            server.login(os.getenv("SMTP_USERNAME"), os.getenv("SMTP_PASSWORD"))
            server.send_message(msg)

        logger.info(f"📧 Email alert sent to {msg['To']}")
    except Exception as e:
        logger.error(f"❌ Failed to send email alert: {e}")

# JSON helpers
def load_json(path):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"❌ Failed to load {path}: {e}")
    return {}

def save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"❌ Failed to save {path}: {e}")

# Main function
def post_due_reels():
    logger.info("📤 Starting scheduled reel poster...")
    schedule = load_json(SCHEDULE_FILE)
    history = load_json(HISTORY_FILE)
    today = datetime.now().strftime("%Y-%m-%d")
    failures = []

    for user_email, jobs in schedule.items():
        if not isinstance(jobs, list):
            logger.warning(f"[{user_email}] ⚠️ Invalid schedule format.")
            continue

        token_data = get_user_token_data(user_email)
        if not token_data or "access_token" not in token_data:
            logger.warning(f"[{user_email}] 🚫 No valid Instagram token.")
            continue

        for item in jobs:
            if not isinstance(item, dict) or item.get("posted"):
                continue

            scheduled_date = item.get("scheduled_for")
            video = item.get("video")
            if not video or not scheduled_date:
                logger.warning(f"[{user_email}] ⚠️ Missing required fields in schedule entry.")
                continue

            if scheduled_date > today:
                continue  # Not due yet

            video_path = os.path.join(OUTPUT_DIR, user_email, "videos", video)
            if not os.path.exists(video_path):
                logger.warning(f"[{user_email}] ❌ Video not found: {video_path}")
                failures.append(f"[{user_email}] Missing file: {video}")
                continue

            caption = item.get("script") or history.get(user_email, {}).get(video, "")
            logger.info(f"[{user_email}] 📲 Posting scheduled reel: {video}")

            try:
                success = post_to_instagram(user_email, video_path, caption)
                if success:
                    item["posted"] = True
                    item["posted_at"] = datetime.now().isoformat()
                    logger.info(f"[{user_email}] ✅ Successfully posted: {video}")
                else:
                    logger.error(f"[{user_email}] ❌ Post API failed: {video}")
                    failures.append(f"[{user_email}] Failed API post: {video}")
            except Exception as e:
                logger.exception(f"[{user_email}] ❌ Exception during post: {video}")
                failures.append(f"[{user_email}] Exception: {str(e)}")

    save_json(SCHEDULE_FILE, schedule)
    logger.info("✅ Finished scheduled posting.")

    if failures:
        send_email_alert("[Alert] Reel Posting Failures", "\n".join(failures))

# Entry point
if __name__ == "__main__":
    post_due_reels()

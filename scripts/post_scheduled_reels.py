# File: scripts/post_scheduled_reels.py

import os
import logging
import smtplib
import sqlite3
from datetime import datetime
from logging.handlers import RotatingFileHandler
from email.mime.text import MIMEText
from dotenv import load_dotenv

from utils.instagram_posting import post_to_instagram
from utils.user_db import get_user_token_data

# Load .env
load_dotenv()

# ---------------------
# Paths and Constants
# ---------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))

DB_PATH = os.path.join(ROOT_DIR, "db", "reelvo.db")
OUTPUT_DIR = os.path.join(ROOT_DIR, "output")
LOG_FILE = os.path.join(BASE_DIR, "logs", "post_scheduled.log")
EMAIL_TEMPLATE = os.path.join(BASE_DIR, "templates", "email_alert_template.txt")

# ---------------------
# Logging Setup
# ---------------------

os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logger = logging.getLogger("scheduled_reels")
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(LOG_FILE, maxBytes=2 * 1024 * 1024, backupCount=3)
handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S"))
logger.addHandler(handler)

# ---------------------
# Email Alerting
# ---------------------

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

# ---------------------
# SQLite Helpers
# ---------------------

def fetch_scheduled_reels(conn):
    """Return all unposted reels scheduled for today or earlier."""
    today = datetime.now().strftime("%Y-%m-%d")
    query = """
        SELECT id, user_email, video, scheduled_for, script
        FROM scheduled_posts
        WHERE posted = 0 AND date(scheduled_for) <= date(?)
    """
    return conn.execute(query, (today,)).fetchall()

def mark_reel_posted(conn, post_id):
    conn.execute("""
        UPDATE scheduled_posts
        SET posted = 1, posted_at = ?
        WHERE id = ?
    """, (datetime.now().isoformat(), post_id))
    conn.commit()

def fetch_reel_history_caption(conn, user_email, video_name):
    result = conn.execute("""
        SELECT caption FROM reel_history
        WHERE user_email = ? AND video = ?
    """, (user_email, video_name)).fetchone()
    return result[0] if result else ""

# ---------------------
# Main Logic
# ---------------------

def post_due_reels():
    logger.info("📤 Starting scheduled reel poster...")
    failures = []

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        posts = fetch_scheduled_reels(conn)

        logger.info(f"📋 Found {len(posts)} due scheduled reels.")

        for row in posts:
            post_id = row["id"]
            user_email = row["user_email"]
            video = row["video"]
            scheduled_date = row["scheduled_for"]
            caption = row["script"] or fetch_reel_history_caption(conn, user_email, video)

            token_data = get_user_token_data(user_email)
            if not token_data or "access_token" not in token_data:
                logger.warning(f"[{user_email}] 🚫 No valid Instagram token.")
                continue

            video_path = os.path.join(OUTPUT_DIR, user_email, "videos", video)
            if not os.path.exists(video_path):
                logger.warning(f"[{user_email}] ❌ Video not found: {video_path}")
                failures.append(f"[{user_email}] Missing file: {video}")
                continue

            logger.info(f"[{user_email}] 📲 Posting scheduled reel: {video}")
            try:
                success = post_to_instagram(user_email, video_path, caption)
                if success:
                    mark_reel_posted(conn, post_id)
                    logger.info(f"[{user_email}] ✅ Successfully posted: {video}")
                else:
                    logger.error(f"[{user_email}] ❌ Post API failed: {video}")
                    failures.append(f"[{user_email}] Failed API post: {video}")
            except Exception as e:
                logger.exception(f"[{user_email}] ❌ Exception during post: {video}")
                failures.append(f"[{user_email}] Exception: {str(e)}")

    logger.info("✅ Finished scheduled posting.")

    if failures:
        send_email_alert("[Alert] Reel Posting Failures", "\n".join(failures))

# ---------------------
# Entry Point
# ---------------------

if __name__ == "__main__":
    post_due_reels()

# File: scripts/post_scheduled_reels.py

"""
Posts scheduled reels using Instagram API, marks them posted,
logs success/failure, and sends email alerts on failures.
"""

import os
import logging
import smtplib
from datetime import datetime
from logging.handlers import RotatingFileHandler
from email.mime.text import MIMEText
from dotenv import load_dotenv

from models import db, init_db
from models.user import User
from models.reel import Reel
from models.schedule import Schedule
from utils.instagram import post_to_instagram
from utils.instagram_db import get_instagram_credentials  # Changed here to ORM-based token fetch

# Load .env
load_dotenv()

# ---------------------
# Paths and Constants
# ---------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
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
# Main Posting Logic
# ---------------------

def post_due_reels():
    logger.info("📤 Starting scheduled reel poster...")

    init_db()  # Initialize DB and create session

    failures = []

    try:
        # Query all schedules where status is 'pending' and scheduled_for <= now
        due_schedules = (
            db.session.query(Schedule)
            .filter(Schedule.status == 'pending')
            .filter(Schedule.scheduled_for <= datetime.now())
            .all()
        )

        logger.info(f"📋 Found {len(due_schedules)} due scheduled reels.")

        for schedule in due_schedules:
            user = db.session.query(User).filter_by(id=schedule.user_id).first()
            reel = db.session.query(Reel).filter_by(id=schedule.reel_id).first()

            if not user or not reel:
                logger.warning(f"Schedule ID {schedule.id} references missing User or Reel.")
                failures.append(f"Schedule ID {schedule.id} missing user or reel")
                continue

            user_email = user.email
            video = os.path.basename(reel.video_path)
            caption = reel.caption or ""

            # Using ORM-based token fetch
            token_data = get_instagram_credentials(user_email)
            if not token_data or "access_token" not in token_data:
                logger.warning(f"[{user_email}] 🚫 No valid Instagram token.")
                failures.append(f"[{user_email}] No valid Instagram token.")
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
                    # Mark schedule and reel as posted
                    schedule.status = 'posted'
                    schedule.error_log = None
                    schedule.retry_count = 0
                    schedule.posted_at = datetime.now()

                    reel.status = 'posted'
                    reel.posted_at = datetime.now()

                    db.session.commit()
                    logger.info(f"[{user_email}] ✅ Successfully posted: {video}")
                else:
                    logger.error(f"[{user_email}] ❌ Post API failed: {video}")
                    schedule.status = 'failed'
                    schedule.error_log = "Post API failure"
                    db.session.commit()
                    failures.append(f"[{user_email}] Failed API post: {video}")

            except Exception as e:
                logger.exception(f"[{user_email}] ❌ Exception during post: {video}")
                schedule.status = 'failed'
                schedule.error_log = str(e)
                db.session.commit()
                failures.append(f"[{user_email}] Exception: {str(e)}")

    except Exception as e:
        logger.error(f"Unexpected error in post_due_reels: {e}")
        failures.append(f"Unexpected error: {str(e)}")

    logger.info("✅ Finished scheduled posting.")

    if failures:
        send_email_alert("[Alert] Reel Posting Failures", "\n".join(failures))


# ---------------------
# Entry Point
# ---------------------

if __name__ == "__main__":
    post_due_reels()

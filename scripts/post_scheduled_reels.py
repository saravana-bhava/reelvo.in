# ================================================
# File:         scripts/post_scheduled_reels.py
# Description:  Post scheduled reels to Instagram automatically
# Framework:    Flask + TailwindCSS
# Version:      1.0.0
# Last Updated: 12 August 2025
# Author:       Saravana Bhava
# Author URL:   https://SazM.in
# ================================================

"""
Posts scheduled reels using Instagram API, marks them as posted,
logs success/failure, and sends email alerts on failures.
"""

import os
import sys
import logging
import smtplib
from datetime import datetime, timezone
from pytz import timezone as pytz_timezone
from logging.handlers import RotatingFileHandler
from email.mime.text import MIMEText
from dotenv import load_dotenv
from flask import Flask

# Project Imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models import db
from models.user import User
from models.reel import Reel
from models.schedule import Schedule
from utils.instagram import post_to_instagram
from utils.instagram_db import get_instagram_credentials

# ---------------------
# Load Config
# ---------------------
load_dotenv()

REQUIRED_ENV_VARS = [
    "MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_HOST", "MYSQL_PORT", "MYSQL_DB",
    "SMTP_HOST", "SMTP_USERNAME", "SMTP_PASSWORD", "SMTP_PORT"
]
missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
if missing_vars:
    raise RuntimeError(f"Missing required environment variables: {', '.join(missing_vars)}")

# ---------------------
# Paths and Constants
# ---------------------
BASE_DIR = os.getenv("BASE_DIR", "/var/www/html")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
EMAIL_TEMPLATE = os.path.join(BASE_DIR, "templates", "email_alert_template.txt")

log_date = datetime.now()
log_dir = os.path.join(BASE_DIR, "logs", log_date.strftime("%Y-%m"))
os.makedirs(log_dir, exist_ok=True)
LOG_FILE = os.path.join(log_dir, f"post_scheduled_{log_date.strftime('%d')}.log")

# ---------------------
# Logging Setup
# ---------------------
logger = logging.getLogger("scheduled_reels")
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(LOG_FILE, maxBytes=2 * 1024 * 1024, backupCount=3)
handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S"))
logger.addHandler(handler)

# ---------------------
# Email Alert
# ---------------------
def send_email_alert(subject, message):
    try:
        if os.path.exists(EMAIL_TEMPLATE):
            with open(EMAIL_TEMPLATE, "r", encoding="utf-8") as f:
                body = f.read().format(log_path=LOG_FILE, error_message=message)
        else:
            body = f"ALERT: {message}\n\nSee logs: {LOG_FILE}"

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
        logger.error(f"❌ Failed to send email alert: {e}", exc_info=True)

# ---------------------
# Flask App Factory
# ---------------------
def create_app():
    app = Flask(__name__)
    user = os.getenv("MYSQL_USER")
    password = os.getenv("MYSQL_PASSWORD")
    host = os.getenv("MYSQL_HOST", "localhost")
    port = os.getenv("MYSQL_PORT", "3306")
    db_name = os.getenv("MYSQL_DB")

    app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    return app

# ---------------------
# Main Posting Logic
# ---------------------
def post_due_reels(app):
    failures = []
    success_count = 0
    use_drive = os.getenv("UPLOAD_TO_DRIVE", "false").lower() == "true"

    with app.app_context():
        try:
            # Convert current UTC time to Asia/Kolkata timezone (naive datetime for DB comparison)
            now_kolkata = datetime.now(timezone.utc).astimezone(pytz_timezone("Asia/Kolkata")).replace(tzinfo=None)

            # Step 1: Lock and claim due schedules (skip locked for concurrency safety)
            due_schedules = (
                db.session.query(Schedule)
                .filter(Schedule.status == 'pending')
                .filter(Schedule.scheduled_for <= now_kolkata)
                .with_for_update(skip_locked=True)
                .all()
            )

            if not due_schedules:
                logger.info("No scheduled reels to post at this time.")
                return

            # Step 2: Mark schedules as processing to prevent re-processing
            for schedule in due_schedules:
                schedule.status = 'processing'
            db.session.commit()

            # Step 3: Post reels to Instagram
            for schedule in due_schedules:
                try:
                    user = db.session.get(User, schedule.user_id)
                    reel = db.session.get(Reel, schedule.reel_id)

                    if not user or not reel:
                        msg = f"Schedule ID {schedule.id} references missing user or reel."
                        logger.warning(msg)
                        failures.append(msg)
                        schedule.status = 'failed'
                        schedule.error_log = msg
                        db.session.commit()
                        continue

                    user_email = user.email
                    caption = reel.caption or ""
                    video_filename = os.path.basename(reel.video_path)
                    video_path = os.path.join(OUTPUT_DIR, user_email, "videos", video_filename)

                    if not os.path.isfile(video_path):
                        msg = f"[{user_email}] Missing video file: {video_path}"
                        logger.warning(msg)
                        failures.append(msg)
                        schedule.status = 'failed'
                        schedule.error_log = msg
                        db.session.commit()
                        continue

                    token_data = get_instagram_credentials(user_email)
                    if not token_data or "access_token" not in token_data:
                        msg = f"[{user_email}] No valid Instagram access token."
                        logger.warning(msg)
                        failures.append(msg)
                        schedule.status = 'failed'
                        schedule.error_log = msg
                        db.session.commit()
                        continue

                    logger.info(f"[{user_email}] ▶ Posting reel: {video_filename}")

                    result = post_to_instagram(
                        reel_id=schedule.reel_id,
                        video_path=video_path,
                        caption=caption,
                        user_email=user_email,
                        video_url=f"https://reelvo.in/videos/{user_email}/{video_filename}",
                        use_drive=use_drive,
                    )

                    if result and "Reel posted successfully" in result:
                        schedule.status = 'posted'
                        schedule.posted_at = datetime.now()
                        schedule.error_log = None
                        schedule.retry_count = 0

                        reel.status = 'posted'
                        reel.posted_at = datetime.now()

                        db.session.commit()
                        success_count += 1
                        logger.info(f"[{user_email}] ✅ Posted successfully: {video_filename}")
                    else:
                        raise RuntimeError(result or "Unknown error from Instagram API")

                except Exception as post_err:
                    logger.error(f"[{user_email}] ❌ Post failed: {video_filename} - {post_err}", exc_info=True)
                    failures.append(f"[{user_email}] Post error: {post_err}")
                    schedule.status = 'failed'
                    schedule.error_log = str(post_err)
                    db.session.commit()

        except Exception as e:
            logger.error("🚨 Fatal error in post_due_reels()", exc_info=True)
            failures.append(f"Fatal exception: {e}")

    # Send alert email if there are failures
    if failures:
        send_email_alert("🚨 Reel Posting Failures", "\n".join(failures))

    logger.info(f"Posting complete. Successes: {success_count}, Failures: {len(failures)}")

# ---------------------
# Entry Point
# ---------------------
if __name__ == "__main__":
    app = create_app()
    post_due_reels(app)

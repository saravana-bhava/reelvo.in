# File: scripts/post_scheduled_reels.py

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

REQUIRED_ENV_VARS = ["DB_URL", "SMTP_HOST", "SMTP_USERNAME", "SMTP_PASSWORD"]
missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
if missing_vars:
    raise RuntimeError(f"Missing required environment variables: {', '.join(missing_vars)}")

# ---------------------
# Paths and Constants
# ---------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
OUTPUT_DIR = os.path.join(ROOT_DIR, "output")
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
        logger.error(f"❌ Failed to send email alert: {e}")

# ---------------------
# Flask App Factory
# ---------------------
def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DB_URL")
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
            now_kolkata = datetime.now(timezone.utc).astimezone(pytz_timezone("Asia/Kolkata")).replace(tzinfo=None)
            due_schedules = (
                db.session.query(Schedule)
                .filter(Schedule.status == 'pending')
                .filter(Schedule.scheduled_for <= now_kolkata)
                .all()
            )

            logger.info(f"📋 Found {len(due_schedules)} due schedules at {now_kolkata}")

            for schedule in due_schedules:
                user = db.session.query(User).get(schedule.user_id)
                reel = db.session.query(Reel).get(schedule.reel_id)

                if not user or not reel:
                    msg = f"Schedule ID {schedule.id} references missing user/reel"
                    logger.warning(msg)
                    failures.append(msg)
                    continue

                user_email = user.email
                caption = reel.caption or ""
                video = os.path.basename(reel.video_path)
                video_path = os.path.join(OUTPUT_DIR, user_email, "videos", video)

                if not os.path.exists(video_path):
                    msg = f"[{user_email}] Missing file: {video_path}"
                    logger.warning(msg)
                    failures.append(msg)
                    continue

                token_data = get_instagram_credentials(user_email)
                if not token_data or "access_token" not in token_data:
                    msg = f"[{user_email}] No valid Instagram token."
                    logger.warning(msg)
                    failures.append(msg)
                    continue

                logger.info(f"[{user_email}] ▶ Posting reel: {video}")
                try:
                    result = post_to_instagram(
                        reel_id=schedule.reel_id,
                        video_path=video_path,
                        caption=caption,
                        user_email=user_email,
                        video_url="",
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
                        logger.info(f"[{user_email}] ✅ Posted successfully: {video}")
                    else:
                        raise ValueError(result or "Unknown error from post API")

                except Exception as e:
                    logger.exception(f"[{user_email}] ❌ Post failed: {video}")
                    schedule.status = 'failed'
                    schedule.error_log = str(e)
                    db.session.commit()
                    failures.append(f"[{user_email}] Post error: {str(e)}")

        except Exception as e:
            logger.exception("🚨 Fatal error in post_due_reels()")
            failures.append(f"Fatal exception: {str(e)}")

        logger.info(f"✅ Done. Success: {success_count}, Failures: {len(failures)}")
        if failures:
            send_email_alert("🚨 Reel Posting Failures", "\n".join(failures))

# ---------------------
# Entry Point
# ---------------------
if __name__ == "__main__":
    app = create_app()
    logger.info(f"⏰ Running post_due_reels at UTC {datetime.now(timezone.utc).isoformat()}")
    post_due_reels(app)

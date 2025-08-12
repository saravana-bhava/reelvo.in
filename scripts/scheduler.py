# ================================================
# File:         scripts/scheduler.py
# Description:  Automate Reel Generation and Scheduling
# Framework:    Flask + TailwindCSS
# Version:      1.0.0
# Last Updated: 31 July 2025
# Author:       Saravana Bhava
# Author URL:   https://SazM.in
# ================================================

"""
Autoamte Reel Generation and Scheduling
"""

import os
import sys
import uuid
from datetime import datetime, timedelta
from threading import Thread
from pytz import timezone, utc
from dotenv import load_dotenv
from flask import Flask

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models import db, AutoPostPlan, Schedule, User
from utils.generate_script import generate_script_for_user
from utils.reel_job import process_reel_job
from flask import current_app

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


def run_reel_job_in_background(app, task_id, user_id, user_email, theme_name, language, script_text,
                              use_tts, voice, custom_voice_file, subtitles_enabled, watermark_enabled):
    with app.app_context():
        process_reel_job(
            task_id,
            user_id,
            user_email,
            theme_name,
            language,
            script_text,
            use_tts,
            voice,
            custom_voice_file,
            subtitles_enabled,
            watermark_enabled
        )


def automate_reels_and_schedule():
    app = current_app._get_current_object()
    active_plans = AutoPostPlan.query.filter_by(status="Active").all()
    user_tz = timezone('Asia/Kolkata')  # Adjust if you store user timezone in plan/user model

    for plan in active_plans:
        user = db.session.get(User, plan.user_id)
        if not user:
            continue

        start_date = plan.start_date
        end_date = plan.end_date()
        today = datetime.utcnow().date()

        # Skip completed plans
        if today > end_date:
            plan.status = "Completed"
            db.session.commit()
            continue

        # Schedule reels from max(today, start_date) to end_date
        current_date = max(today, start_date)
        while current_date <= end_date:
            # Compose scheduled datetime localized & converted to UTC
            scheduled_local = datetime.combine(current_date, plan.auto_post_time)
            scheduled_local = user_tz.localize(scheduled_local)
            scheduled_utc = scheduled_local.astimezone(utc)

            # Check if already scheduled
            existing = Schedule.query.filter_by(
                user_id=plan.user_id,
                scheduled_for=scheduled_utc,
                status='pending'
            ).first()
            if existing:
                current_date += timedelta(days=1)
                continue

            # Generate unique theme_name
            raw_topic = plan.topic or "default"
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            theme_name = f"{raw_topic.replace(' ', '_').lower()}_{timestamp}"

            # Generate script file path using your utility to keep consistency
            script_path = generate_script_for_user(
                user_email=user.email,
                folder_name="scripts",
                theme_name=theme_name,
                language=plan.language,
                prompt=plan.topic
            )
            with open(script_path, encoding="utf-8") as f:
                script_text = f.read()

            # Voice settings
            use_tts = True
            voice = plan.voice_artist
            custom_voice_file = None  # No file upload in automation

            # Subtitle and watermark
            subtitles_enabled = plan.subtitles_enabled
            watermark_enabled = plan.watermark_enabled

            # Generate task id
            task_id = str(uuid.uuid4())

            # Start reel generation in background thread
#            thread = Thread(
#                target=run_reel_job_in_background,
#                args=(
#                    app, task_id, plan.user_id, user.email,
#                    theme_name, plan.language, script_text,
#                    use_tts, voice, custom_voice_file,
#                    subtitles_enabled, watermark_enabled
#                )
#            )
#            thread.daemon = True
#            thread.start()

            # Wait a little or manage concurrency if needed
            # For now, just proceed

            # The Schedule record will be created inside process_reel_job with scheduled_for=None
            # Update the Schedule to set correct scheduled_for
            # We find latest Schedule for user after starting thread and update it

            # Wait briefly for reel creation to flush Schedule entry
            import time
            time.sleep(1)

            schedule = Schedule.query.filter_by(user_id=plan.user_id).order_by(Schedule.id.desc()).first()
            if schedule:
                schedule.scheduled_for = scheduled_utc
                db.session.commit()

            current_date += timedelta(days=1)

    # Commit plan status updates if any
    db.session.commit()

# ---------------------
# Entry Point
# ---------------------
if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        automate_reels_and_schedule()

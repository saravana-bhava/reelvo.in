# ================================================
# File:         scripts/auto_generate_schedule_reels.py
# Description:  Automate Reel Generation and Scheduling
# Framework:    Flask + TailwindCSS
# Version:      1.1.0
# Last Updated: 12 August 2025
# Author:       Saravana Bhava
# Author URL:   https://SazM.in
# ================================================

"""
Automate Reel Generation and Scheduling

This script fetches active auto-post plans, generates scripts, schedules reels, and
starts background threads for reel generation jobs.
"""

import os
import sys
import uuid
import logging
from datetime import datetime, timedelta
from threading import Thread
from dotenv import load_dotenv
from flask import Flask

# Add parent directory to sys.path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models import db, AutoPostPlan, Schedule, User
from utils.generate_script import generate_script_for_user
from utils.reel_job import process_reel_job

# ---------------------
# Load environment variables safely
# ---------------------
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ---------------------
# Flask App Factory
# ---------------------
def create_app():
    app = Flask(__name__)

    # Load DB config from environment variables with safe defaults
    user = os.getenv("MYSQL_USER")
    password = os.getenv("MYSQL_PASSWORD")
    host = os.getenv("MYSQL_HOST", "localhost")
    port = os.getenv("MYSQL_PORT", "3306")
    db_name = os.getenv("MYSQL_DB")

    if not all([user, password, db_name]):
        logger.error("Database credentials (MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB) are not fully set in environment.")
        sys.exit(1)

    app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    return app


def run_reel_job_in_background(
    app, task_id, user_id, user_email, theme_name, language, script_text,
    use_tts, voice, custom_voice_file, subtitles_enabled, watermark_enabled, scheduled_time
):
    try:
        with app.app_context():
            logger.info(f"Starting reel job for task_id={task_id}, user_id={user_id}")
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
                watermark_enabled,
                scheduled_time=scheduled_time
            )
            logger.info(f"Finished reel job for task_id={task_id}")
    except Exception as e:
        logger.error(f"Error in reel job for task_id={task_id}: {e}", exc_info=True)


def automate_reels_and_schedule():
    logger.info("Starting automation of reels and scheduling.")
    app = create_app()
    with app.app_context():
        try:
            active_plans = AutoPostPlan.query.filter_by(status="Active").all()
            logger.info(f"Found {len(active_plans)} active auto-post plans.")

            today = datetime.utcnow().date()
            next_day = today + timedelta(days=1)

            for plan in active_plans:
                try:
                    user = db.session.get(User, plan.user_id)
                    if not user:
                        logger.warning(f"User with id {plan.user_id} not found. Skipping plan id {plan.id}.")
                        continue

                    start_date = plan.start_date
                    end_date = plan.end_date()

                    # Skip completed plans
                    if today > end_date:
                        plan.status = "Completed"
                        db.session.commit()
                        logger.info(f"Marked plan id {plan.id} as Completed (end date passed).")
                        continue

                    # Only schedule reels for next day if it falls within plan duration
                    if not (start_date <= next_day <= end_date):
                        logger.debug(f"Next day {next_day} is outside plan duration for plan id {plan.id}. Skipping.")
                        continue

                    current_date = next_day

                    # Compose scheduled datetime in UTC (assuming auto_post_time is naive local time)
                    scheduled_local = datetime.combine(current_date, plan.auto_post_time)

                    # Check if already scheduled
                    existing = Schedule.query.filter_by(
                        user_id=plan.user_id,
                        scheduled_for=scheduled_local,
                        status='pending'
                    ).first()
                    if existing:
                        logger.debug(f"Schedule already exists for user {plan.user_id} at {scheduled_local}. Skipping.")
                        continue

                    # Generate unique theme_name
                    raw_topic = plan.topic or "default"
                    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
                    theme_name = f"{raw_topic.replace(' ', '_').lower()}_{timestamp}"

                    # Generate script file path
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
                    custom_voice_file = None  # No custom voice file upload in automation

                    # Subtitle and watermark flags
                    subtitles_enabled = plan.subtitles_enabled
                    watermark_enabled = plan.watermark_enabled

                    # Generate task id
                    task_id = str(uuid.uuid4())

                    # Run reel generation job threaded in background
                    thread = Thread(
                        target=run_reel_job_in_background,
                        args=(
                            app, task_id, plan.user_id, user.email,
                            theme_name, plan.language, script_text,
                            use_tts, voice, custom_voice_file,
                            subtitles_enabled, watermark_enabled, scheduled_local
                        ),
                        daemon=True
                    )
                    thread.start()

                    logger.info(f"Started background reel job thread for plan id {plan.id}, task_id {task_id}")

                except Exception as inner_exc:
                    logger.error(f"Error processing plan id {plan.id}: {inner_exc}", exc_info=True)

            db.session.commit()
            logger.info("Completed automation cycle.")

        except Exception as e:
            logger.error(f"Unexpected error in automate_reels_and_schedule: {e}", exc_info=True)


# ---------------------
# Entry Point
# ---------------------
if __name__ == "__main__":
    automate_reels_and_schedule()

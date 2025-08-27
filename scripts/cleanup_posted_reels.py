# ================================================
# File:         scripts/cleanup_posted_reels.py
# Description:  Mark reels as deleted 24h after posting
# Framework:    Flask + TailwindCSS
# Version:      1.0.0
# Last Updated: 27 August 2025
# Author:       Saravana Bhava
# ================================================

import os
import sys
import logging
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
from flask import Flask

# Project Imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models import db
from models.reel import Reel
from models.schedule import Schedule

# ---------------------
# Load Config
# ---------------------
load_dotenv()

BASE_DIR = os.getenv("BASE_DIR", "/var/www/html")

log_date = datetime.now()
log_dir = os.path.join(BASE_DIR, "logs", log_date.strftime("%Y-%m"))
os.makedirs(log_dir, exist_ok=True)
LOG_FILE = os.path.join(log_dir, f"cleanup_{log_date.strftime('%d')}.log")

# ---------------------
# Logging Setup
# ---------------------
logger = logging.getLogger("cleanup_reels")
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(LOG_FILE, maxBytes=1 * 1024 * 1024, backupCount=3)
handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S"))
logger.addHandler(handler)

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
# Cleanup Logic
# ---------------------
def cleanup_reels(app):
    with app.app_context():
        try:
            cutoff = datetime.now() - timedelta(hours=24)  # 24h

            # Get reels eligible for deletion
            reels_to_delete = (
                db.session.query(Reel)
                .filter(Reel.status == "posted")
                .filter(Reel.posted_at < cutoff)
                .all()
            )

            if not reels_to_delete:
                logger.info("No reels to mark as deleted.")
                return

            for reel in reels_to_delete:
                # Delete associated schedules
                schedules = db.session.query(Schedule).filter(Schedule.reel_id == reel.id).all()
                for sched in schedules:
                    logger.info(f"❌ Deleting schedule ID={sched.id} for reel ID={reel.id}")
                    db.session.delete(sched)

                # Mark reel as deleted
                logger.info(f"🗑️ Marking reel ID={reel.id} as deleted (User={reel.user_id})")
                reel.status = "deleted"

            # Commit all changes at once
            try:
                db.session.commit()
                logger.info(f"✅ {len(reels_to_delete)} reels marked as deleted and associated schedules removed")
            except Exception as e:
                logger.error("❌ Commit failed", exc_info=True)

        except Exception as e:
            logger.error("❌ Error during cleanup", exc_info=True)

# ---------------------
# Entry Point
# ---------------------
if __name__ == "__main__":
    app = create_app()
    cleanup_reels(app)

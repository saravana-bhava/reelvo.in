"""
Assigns posting times for unscheduled reels (1 per day at 4PM).
Schedules reels by creating entries in `schedules` table using SQLAlchemy ORM.
Usage:
    python scripts/schedule_reels.py <user_email>
"""

import os
import sys
import logging
from datetime import datetime, timedelta

from models import db, init_db
from models.user import User
from models.reel import Reel
from models.schedule import Schedule

# Constants
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_POST_HOUR = 16  # 4PM

# Setup logging
LOG_PATH = os.path.join(ROOT_DIR, "scheduler", "logs", "schedule_reels.log")
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_PATH), logging.StreamHandler()],
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("schedule_reels")

def schedule_reels_for_user(user_email: str):
    # Initialize DB if needed (depends on your app setup)
    init_db()

    with db.session.no_autoflush:
        user = db.session.query(User).filter(User.email == user_email).first()
        if not user:
            logger.warning(f"[{user_email}] ⚠️ User not found.")
            return

        # Get reels for user that are NOT already scheduled
        # We consider reels with status='draft' or 'posted' but NOT scheduled in schedules table
        scheduled_reel_ids = {s.reel_id for s in db.session.query(Schedule).filter(Schedule.user_id == user.id).all()}
        unscheduled_reels = (
            db.session.query(Reel)
            .filter(Reel.user_id == user.id)
            .filter(~Reel.id.in_(scheduled_reel_ids))
            .order_by(Reel.created_at.asc())
            .all()
        )

        if not unscheduled_reels:
            logger.info(f"[{user_email}] ℹ️ No new reels to schedule.")
            return

        # Determine starting scheduled date (4 PM today or next day after last scheduled)
        last_schedule = (
            db.session.query(Schedule)
            .filter(Schedule.user_id == user.id)
            .order_by(Schedule.scheduled_for.desc())
            .first()
        )

        start_date = datetime.now().replace(hour=DEFAULT_POST_HOUR, minute=0, second=0, microsecond=0)
        if last_schedule and last_schedule.scheduled_for:
            next_date = last_schedule.scheduled_for + timedelta(days=1)
            if next_date > start_date:
                start_date = next_date

        count = 0
        for reel in unscheduled_reels:
            scheduled_for = start_date

            schedule_entry = Schedule(
                user_id=user.id,
                reel_id=reel.id,
                scheduled_for=scheduled_for,
                timezone='Asia/Kolkata',
                status='pending'
            )
            db.session.add(schedule_entry)

            # Mark reel as scheduled (optional, if you want to mark in reels table)
            reel.is_scheduled = True
            reel.scheduled_at = scheduled_for
            reel.status = 'scheduled'

            start_date += timedelta(days=1)
            count += 1

        db.session.commit()

        logger.info(f"[{user_email}] ✅ Scheduled {count} new reel(s).")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/schedule_reels.py <user_email>")
        sys.exit(1)

    email = sys.argv[1].strip().lower()
    schedule_reels_for_user(email)

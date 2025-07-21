# File: utils/scheduler.py

"""
Background scheduler that checks the 'reels' SQLite table and auto-posts to Instagram.
Runs in a loop, posting when the scheduled time is met.
"""

import os
import time
import logging
from datetime import datetime
from utils.instagram import post_to_instagram
from utils.reel_history import add_reel_to_history
from utils.user_db_sql import get_db_connection

# Logging
logger = logging.getLogger("scheduler")
logging.basicConfig(level=logging.INFO)


def scheduler_runner() -> None:
    """
    Continuously checks and posts reels from the SQLite 'reels' table
    where is_scheduled = 1 and status = 'scheduled'.
    """
    logger.info("⏱️ Starting background scheduler (SQLite)...")

    while True:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Fetch due reels
            cursor.execute("""
                SELECT * FROM reels
                WHERE is_scheduled = 1
                  AND status = 'scheduled'
                  AND scheduled_at <= CURRENT_TIMESTAMP
            """)
            due_reels = cursor.fetchall()

            for reel in due_reels:
                reel_id = reel["id"]
                user_id = reel["user_id"]
                title = reel["title"]
                video_path = reel["video_path"]
                caption = reel["caption"]
                script = reel["script"]
                scheduled_time = reel["scheduled_at"]

                try:
                    logger.info(f"📤 Posting scheduled reel → ID={reel_id} | User={user_id} | Title={title}")

                    result = post_to_instagram(
                        video_path=video_path,
                        caption=caption,
                        user_id=user_id
                    )

                    permalink = result.get("permalink") if isinstance(result, dict) else None

                    # Mark as posted
                    cursor.execute("""
                        UPDATE reels
                        SET status = 'posted',
                            posted_at = CURRENT_TIMESTAMP,
                            error_log = NULL
                        WHERE id = ?
                    """, (reel_id,))
                    conn.commit()

                    # Log to history
                    add_reel_to_history(
                        user_id=user_id,
                        filename=os.path.basename(video_path),
                        script=script,
                        caption=caption,
                        permalink=permalink,
                        timestamp=datetime.utcnow().isoformat() + "Z"
                    )

                    logger.info(f"[✅] Reel posted → ID={reel_id} | {os.path.basename(video_path)}")

                except Exception as e:
                    logger.error(f"[❌] Failed to post reel ID={reel_id}: {e}")
                    cursor.execute("""
                        UPDATE reels
                        SET status = 'failed',
                            error_log = ?
                        WHERE id = ?
                    """, (str(e), reel_id))
                    conn.commit()

            conn.close()

        except Exception as e:
            logger.warning(f"[⚠️] Scheduler loop error: {e}")

        time.sleep(60)  # Check every minute

# File: utils/instagram_store.py

"""
Handles saving and retrieving Instagram credentials and logging reel post history.
Now stores user account data and reel logs in SQLite under /db/reels.db.
"""

import os
import sqlite3
import logging
from datetime import datetime
from typing import Optional, Dict, Any

# Logger setup
logger = logging.getLogger("instagram_store")
logging.basicConfig(level=logging.INFO)

# Database path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(BASE_DIR, "db", "app.db")

# Ensure DB directory exists
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# Initialize tables
def _init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # Credentials table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS instagram_accounts (
                user_email TEXT PRIMARY KEY,
                access_token TEXT NOT NULL,
                ig_account_id TEXT NOT NULL
            )
        """)
        # Post history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reel_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT NOT NULL,
                video_path TEXT,
                caption TEXT,
                permalink TEXT,
                timestamp TEXT
            )
        """)
        conn.commit()

_init_db()

def save_instagram_credentials(user_email: str, access_token: str, ig_account_id: str) -> None:
    """
    Save Instagram access token and IG business account ID for the user.
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO instagram_accounts (user_email, access_token, ig_account_id)
                VALUES (?, ?, ?)
                ON CONFLICT(user_email) DO UPDATE SET
                    access_token = excluded.access_token,
                    ig_account_id = excluded.ig_account_id
            """, (user_email, access_token, ig_account_id))
            conn.commit()
        logger.info(f"[✅] IG credentials saved for user: {user_email}")
    except Exception as e:
        logger.exception(f"[❌] Failed to save IG credentials for {user_email}: {e}")


def get_instagram_credentials(user_email: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve Instagram credentials (access token, IG account ID) for a user.
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT access_token, ig_account_id
                FROM instagram_accounts
                WHERE user_email = ?
            """, (user_email,))
            row = cursor.fetchone()
            if row:
                return {
                    "access_token": row[0],
                    "user_id": row[1]  # Keep the key name consistent with usage
                }
    except Exception as e:
        logger.exception(f"[❌] Failed to fetch IG credentials for {user_email}: {e}")
    return None


def log_post(user_email: str, video_path: str, caption: str, drive_url: str) -> None:
    """
    Log a successful Instagram post by the user.
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO reel_posts (user_email, video_path, caption, permalink, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (
                user_email,
                video_path,
                caption,
                drive_url,
                datetime.utcnow().isoformat() + "Z"
            ))
            conn.commit()
        logger.info(f"[📦] Logged post for {user_email}: {drive_url}")
    except Exception as e:
        logger.exception(f"[❌] Failed to log post for {user_email}: {e}")

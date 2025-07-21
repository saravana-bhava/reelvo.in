# File: utils/reel_history.py

"""
Handles reading and writing reel history for users using SQLite.
Stores script text, caption, permalink, and timestamp per user and reel.
"""

import os
import sqlite3
from typing import Dict, List, Optional

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "..", "db")
DB_PATH = os.path.join(DB_DIR, "reelvo.db")
os.makedirs(DB_DIR, exist_ok=True)


def _get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _initialize_db():
    conn = _get_connection()
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reel_history (
                user_email TEXT NOT NULL,
                filename TEXT NOT NULL,
                script TEXT,
                caption TEXT,
                permalink TEXT,
                timestamp TEXT,
                PRIMARY KEY (user_email, filename)
            )
        """)
    conn.close()


_initialize_db()


def add_reel_to_history(
    user_email: str,
    filename: str,
    script: str,
    caption: Optional[str] = None,
    permalink: Optional[str] = None,
    timestamp: Optional[str] = None
) -> None:
    conn = _get_connection()
    with conn:
        conn.execute("""
            INSERT OR REPLACE INTO reel_history
            (user_email, filename, script, caption, permalink, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user_email.strip(),
            filename.strip(),
            script.strip(),
            caption or "",
            permalink or "",
            timestamp or ""
        ))
    conn.close()


def list_user_reels(user_email: str) -> List[str]:
    conn = _get_connection()
    cur = conn.cursor()
    cur.execute("SELECT filename FROM reel_history WHERE user_email = ?", (user_email.strip(),))
    filenames = [row["filename"] for row in cur.fetchall()]
    conn.close()
    return filenames


def get_user_script(user_email: str, filename: str) -> Optional[str]:
    conn = _get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT script FROM reel_history
        WHERE user_email = ? AND filename = ?
    """, (user_email.strip(), filename.strip()))
    row = cur.fetchone()
    conn.close()
    return row["script"] if row else None


def get_user_reel_data(user_email: str, filename: str) -> Optional[Dict[str, str]]:
    conn = _get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT script, caption, permalink, timestamp
        FROM reel_history
        WHERE user_email = ? AND filename = ?
    """, (user_email.strip(), filename.strip()))
    row = cur.fetchone()
    conn.close()

    if row:
        return {
            "script": row["script"],
            "caption": row["caption"],
            "permalink": row["permalink"],
            "timestamp": row["timestamp"]
        }
    return None

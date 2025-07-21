# File: utils/user_db_sql.py

import sqlite3
from datetime import datetime, timedelta
from utils.db import get_db_connection

def get_instagram_credentials(user_email):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT u.id as user_id, t.access_token, t.expires_at, t.instagram_user_id
        FROM users u
        JOIN instagram_tokens t ON u.id = t.user_id
        WHERE u.email = ?
    """, (user_email,))

    row = cur.fetchone()
    conn.close()
    if not row:
        return None

    return {
        "access_token": row["access_token"],
        "expires_at": row["expires_at"],
        "ig_user_id": row["instagram_user_id"]
    }

def update_instagram_tokens(user_email, access_token, refresh_token="", expires_in=5184000):
    """
    Updates or inserts Instagram access tokens for the given user.

    Parameters:
        user_email (str): Email of the user (must already exist in users table).
        access_token (str): Long-lived access token.
        refresh_token (str): Optional, not currently used.
        expires_in (int): Lifetime of the token in seconds (default: 60 days).
    """
    conn = get_db_connection()
    cur = conn.cursor()

    # Get user_id from email
    cur.execute("SELECT id FROM users WHERE email = ?", (user_email,))
    row = cur.fetchone()
    if not row:
        conn.close()
        raise ValueError(f"User with email {user_email} not found")

    user_id = row["id"]
    now = datetime.utcnow()
    expires_at = now + timedelta(seconds=expires_in)

    # Check if record exists
    cur.execute("SELECT id FROM instagram_tokens WHERE user_id = ?", (user_id,))
    existing = cur.fetchone()

    if existing:
        # Update
        cur.execute("""
            UPDATE instagram_tokens
            SET access_token = ?, refresh_token = ?, expires_at = ?, updated_at = ?
            WHERE user_id = ?
        """, (access_token, refresh_token, expires_at.isoformat(), now.isoformat(), user_id))
    else:
        # Insert
        cur.execute("""
            INSERT INTO instagram_tokens (user_id, access_token, refresh_token, expires_at, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, access_token, refresh_token, expires_at.isoformat(), now.isoformat(), now.isoformat()))

    conn.commit()
    conn.close()

def log_post_to_db(user_email, video_path, caption, platform, permalink):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE email = ?", (user_email,))
    row = cur.fetchone()
    if not row:
        conn.close()
        raise ValueError(f"User with email {user_email} not found")

    user_id = row["id"]
    now = datetime.utcnow()

    cur.execute("""
        INSERT INTO reels (user_id, video_path, caption, platform, permalink, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, video_path, caption, platform, permalink, now.isoformat()))

    conn.commit()
    conn.close()

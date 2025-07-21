# File: scripts/init_db.py

import sqlite3
import os

DB_PATH = "db/reelvo.db"

def create_db_if_not_exists():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    if not os.path.exists(DB_PATH):
        open(DB_PATH, "w").close()

def init_users_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

def init_scheduled_posts_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS scheduled_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            video TEXT NOT NULL,
            script TEXT,
            scheduled_for TIMESTAMP NOT NULL,
            posted INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

def init_instagram_tokens_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS instagram_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            access_token TEXT NOT NULL,
            refresh_token TEXT,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

def init_progress_status_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS progress_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            video_name TEXT NOT NULL,
            status TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

def main():
    create_db_if_not_exists()
    with sqlite3.connect(DB_PATH) as conn:
        init_users_table(conn)
        init_scheduled_posts_table(conn)
        init_instagram_tokens_table(conn)
        init_progress_status_table(conn)
        print("✅ All necessary tables have been created or verified.")

if __name__ == "__main__":
    main()

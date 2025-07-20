# File: scripts/insert_fallback_themes.py

import json
import os
import sqlite3

DB_PATH = os.path.join("db", "app.db")

def get_db_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def create_themes_table_if_not_exists(conn):
    conn.execute('''
        CREATE TABLE IF NOT EXISTS themes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT NOT NULL,
            lang TEXT NOT NULL,
            content TEXT NOT NULL,
            UNIQUE(key, lang)
        )
    ''')
    conn.commit()

def insert_fallback_themes():
    with open('theme.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    conn = get_db_conn()
    create_themes_table_if_not_exists(conn)
    inserted = 0

    for key, langs in data.items():
        for lang, content in langs.items():
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO themes (key, lang, content) VALUES (?, ?, ?)",
                    (key, lang, content)
                )
                inserted += 1
            except Exception as e:
                print(f"❌ Failed to insert ({key}, {lang}): {e}")

    conn.commit()
    conn.close()
    print(f"✅ Inserted {inserted} fallback theme rows.")

if __name__ == "__main__":
    insert_fallback_themes()

# File: utils/instagram_store.py

"""
Handles saving and retrieving Instagram credentials and logging reel post history.
Stores user account data and reel logs in JSON format under /db directory.
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional

# Logger setup
logger = logging.getLogger("instagram_store")
logging.basicConfig(level=logging.INFO)

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "..", "db")
ACCOUNTS_FILE = os.path.join(DB_DIR, "user_accounts.json")
HISTORY_FILE = os.path.join(DB_DIR, "reel_history.json")

# Ensure required directories and files exist
os.makedirs(DB_DIR, exist_ok=True)
for file_path in [ACCOUNTS_FILE, HISTORY_FILE]:
    if not os.path.exists(file_path):
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump({}, f)


def save_instagram_credentials(username: str, access_token: str, ig_account_id: str) -> None:
    """
    Save Instagram access token and IG business account ID for the user.
    """
    try:
        with open(ACCOUNTS_FILE, "r+", encoding="utf-8") as f:
            data = json.load(f)
            data[username] = {
                "access_token": access_token,
                "ig_account_id": ig_account_id
            }
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()
        logger.info(f"[✅] IG credentials saved for user: {username}")
    except Exception as e:
        logger.exception(f"[❌] Failed to save IG credentials for {username}: {e}")


def get_instagram_credentials(username: str) -> Optional[dict]:
    """
    Retrieve Instagram credentials (access token, IG account ID) for a user.
    """
    try:
        with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get(username)
    except Exception as e:
        logger.exception(f"[❌] Failed to read IG credentials for {username}: {e}")
        return None


def log_post(username: str, video_path: str, caption: str, drive_url: str) -> None:
    """
    Log a successful Instagram post by the user.

    Args:
        username (str): Username of the poster
        video_path (str): Path to local video file
        caption (str): Caption posted
        drive_url (str): Instagram permalink
    """
    try:
        with open(HISTORY_FILE, "r+", encoding="utf-8") as f:
            data = json.load(f)
            if username not in data:
                data[username] = []

            data[username].append({
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "video_path": video_path,
                "caption": caption,
                "permalink": drive_url
            })

            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()

        logger.info(f"[📦] Logged post for {username}: {drive_url}")
    except Exception as e:
        logger.exception(f"[❌] Failed to log post for {username}: {e}")

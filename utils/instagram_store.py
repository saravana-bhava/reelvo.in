# File: utils/instagram_store.py

"""
Handles saving and retrieving Instagram credentials and logging reel post history.
Stores data in JSON files under /db directory.
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional

# Setup logging
logger = logging.getLogger("instagram_store")
logging.basicConfig(level=logging.INFO)

# Paths
DB_DIR = os.path.join(os.path.dirname(__file__), "..", "db")
ACCOUNTS_FILE = os.path.join(DB_DIR, "user_accounts.json")
HISTORY_FILE = os.path.join(DB_DIR, "reel_history.json")

# Ensure directory and files exist
os.makedirs(DB_DIR, exist_ok=True)
for file_path in [ACCOUNTS_FILE, HISTORY_FILE]:
    if not os.path.exists(file_path):
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump({}, f)


def save_instagram_credentials(username: str, access_token: str, ig_account_id: str) -> None:
    """
    Saves the user's Instagram API credentials.

    Args:
        username (str): App username
        access_token (str): Instagram long-lived access token
        ig_account_id (str): Instagram Business Account ID
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
        logger.error(f"[❌] Failed to save IG credentials: {e}")


def get_instagram_credentials(username: str) -> Optional[dict]:
    """
    Retrieves Instagram credentials for a user.

    Args:
        username (str): App username

    Returns:
        dict: Contains 'access_token' and 'ig_account_id', or None
    """
    try:
        with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get(username)
    except Exception as e:
        logger.error(f"[❌] Failed to read IG credentials: {e}")
        return None


def log_post(username: str, category: str, permalink: str) -> None:
    """
    Logs an Instagram reel post.

    Args:
        username (str): App username
        category (str): Reel category/theme
        permalink (str): Instagram permalink of the posted reel
    """
    try:
        with open(HISTORY_FILE, "r+", encoding="utf-8") as f:
            data = json.load(f)
            if username not in data:
                data[username] = []

            data[username].append({
                "category": category,
                "permalink": permalink,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })

            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()

        logger.info(f"[📦] Logged post for {username}: {permalink}")
    except Exception as e:
        logger.error(f"[❌] Failed to log post: {e}")

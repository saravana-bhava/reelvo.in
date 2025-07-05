# File: utils/instagram_store.py

"""
Handles saving and retrieving Instagram credentials and logging reel post history.
Stores user account data and reel logs in JSON format under /db directory.
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any

# Logger setup
logger = logging.getLogger("instagram_store")
logging.basicConfig(level=logging.INFO)

# Paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_DIR = os.path.join(BASE_DIR, "db")
ACCOUNTS_FILE = os.path.join(DB_DIR, "user_accounts.json")
HISTORY_FILE = os.path.join(DB_DIR, "reel_history.json")

# Ensure directories and files exist
os.makedirs(DB_DIR, exist_ok=True)
for path in [ACCOUNTS_FILE, HISTORY_FILE]:
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump({}, f)


def _safe_read_json(file_path: str) -> Dict[str, Any]:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        logger.warning(f"[⚠️] Corrupt JSON in {file_path}, resetting.")
        return {}
    except Exception as e:
        logger.exception(f"[❌] Failed to read JSON: {file_path}: {e}")
        return {}


def _safe_write_json(file_path: str, data: dict) -> None:
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.exception(f"[❌] Failed to write JSON: {file_path}: {e}")


def save_instagram_credentials(user_name: str, access_token: str, ig_account_id: str) -> None:
    """
    Save Instagram access token and IG business account ID for the user.
    """
    data = _safe_read_json(ACCOUNTS_FILE)
    data[user_name] = {
        "access_token": access_token,
        "ig_account_id": ig_account_id
    }
    _safe_write_json(ACCOUNTS_FILE, data)
    logger.info(f"[✅] IG credentials saved for user: {user_name}")


def get_instagram_credentials(user_name: str) -> Optional[dict]:
    """
    Retrieve Instagram credentials (access token, IG account ID) for a user.
    """
    data = _safe_read_json(ACCOUNTS_FILE)
    return data.get(user_name)


def log_post(user_name: str, video_path: str, caption: str, drive_url: str) -> None:
    """
    Log a successful Instagram post by the user.

    Args:
        user_name (str): user_name of the poster
        video_path (str): Path to local video file
        caption (str): Caption posted
        drive_url (str): Instagram permalink
    """
    data = _safe_read_json(HISTORY_FILE)

    if user_name not in data:
        data[user_name] = []

    data[user_name].append({
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "video_path": video_path,
        "caption": caption,
        "permalink": drive_url
    })

    _safe_write_json(HISTORY_FILE, data)
    logger.info(f"[📦] Logged post for {user_name}: {drive_url}")

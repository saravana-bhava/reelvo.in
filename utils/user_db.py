# File: utils/user_db.py

"""
Handles saving and retrieving user Instagram tokens (access, refresh, expiration).
Uses JSON files for simplicity.
"""

import os
import json
from datetime import datetime, timedelta
from typing import Optional

USER_DB_DIR = "user_tokens"
os.makedirs(USER_DB_DIR, exist_ok=True)


def get_user_token_path(user_name: str) -> str:
    """Returns the path to the user's token JSON file."""
    return os.path.join(USER_DB_DIR, f"{user_name}.json")


def save_user_tokens(user_name: str, access_token: str, refresh_token: str, expires_in: int):
    """
    Save user's Instagram access & refresh tokens.

    Args:
        user_name (str): Unique user ID.
        access_token (str): Access token from Instagram API.
        refresh_token (str): Long-lived refresh token (if available).
        expires_in (int): Expiration in seconds.
    """
    path = get_user_token_path(user_name)
    data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_at": (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat()
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_user_tokens(user_name: str) -> Optional[dict]:
    """
    Load tokens from file.

    Args:
        user_name (str): Unique user ID.

    Returns:
        dict or None: Token dict or None if not found.
    """
    path = get_user_token_path(user_name)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def update_access_token(user_name: str, new_token: str, new_expiry: int):
    """
    Update user's access token and expiry time.

    Args:
        user_name (str): User ID.
        new_token (str): New access token.
        new_expiry (int): New expiry in seconds.
    """
    tokens = load_user_tokens(user_name)
    if tokens:
        tokens["access_token"] = new_token
        tokens["expires_at"] = (datetime.utcnow() + timedelta(seconds=new_expiry)).isoformat()
        with open(get_user_token_path(user_name), "w", encoding="utf-8") as f:
            json.dump(tokens, f, indent=2)


def get_instagram_credentials(user_name: str) -> Optional[dict]:
    """
    Get access token for use with Instagram Graph API.

    Args:
        user_name (str): User ID.

    Returns:
        dict or None: {"access_token": str} or None.
    """
    tokens = load_user_tokens(user_name)
    if not tokens or "access_token" not in tokens:
        return None
    return {"access_token": tokens["access_token"]}


def log_post(user_name: str, video_path: str, caption: str, drive_url: str = ""):
    """
    Append a post log entry.

    Args:
        user_name (str): User ID.
        video_path (str): Path to local MP4 file.
        caption (str): Reel caption.
        drive_url (str): Optional Google Drive share URL.
    """
    log_dir = os.path.join("output", user_name)
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "instagram_posts.log")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"{datetime.utcnow().isoformat()} | {video_path} | {caption} | {drive_url or 'N/A'}\n")

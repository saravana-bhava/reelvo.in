# File: utils/user_db.py

"""
Handles saving and retrieving user Instagram tokens (access, refresh, expiration).
Uses JSON files for simplicity.
"""

import os
import json
from datetime import datetime, timedelta
from typing import Optional

# Directory: Base = project root
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "output"))  # output/

def get_user_output_dir(user_email: str) -> str:
    """Return the base output dir for the user."""
    return os.path.join(OUTPUT_DIR, user_email)

def get_user_token_path(user_email: str) -> str:
    """Returns the path to the user's token JSON file inside output/<email>/"""
    return os.path.join(get_user_output_dir(user_email), "user_tokens.json")

def get_user_log_path(user_email: str) -> str:
    """Returns the path to the user's log file inside output/<email>/"""
    return os.path.join(get_user_output_dir(user_email), "reel_logs.log")


def save_user_tokens(user_email: str, access_token: str, refresh_token: str, expires_in: int):
    """
    Save user's Instagram access & refresh tokens.

    Args:
        user_email (str): Unique user ID.
        access_token (str): Access token from Instagram API.
        refresh_token (str): Long-lived refresh token (if available).
        expires_in (int): Expiration in seconds.
    """
    path = get_user_token_path(user_email)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_at": (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat()
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_user_tokens(user_email: str) -> Optional[dict]:
    """
    Load tokens from file.

    Args:
        user_email (str): Unique user ID.

    Returns:
        dict or None: Token dict or None if not found or invalid.
    """
    path = get_user_token_path(user_email)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def update_access_token(user_email: str, new_token: str, new_expiry: int):
    """
    Update user's access token and expiry time.

    Args:
        user_email (str): User ID.
        new_token (str): New access token.
        new_expiry (int): New expiry in seconds.
    """
    tokens = load_user_tokens(user_email)
    if tokens:
        tokens["access_token"] = new_token
        tokens["expires_at"] = (datetime.utcnow() + timedelta(seconds=new_expiry)).isoformat()
        with open(get_user_token_path(user_email), "w", encoding="utf-8") as f:
            json.dump(tokens, f, indent=2)


def is_token_expired(user_email: str) -> bool:
    """
    Check whether a user's token has expired.

    Args:
        user_email (str): User ID.

    Returns:
        bool: True if expired or invalid, else False.
    """
    tokens = load_user_tokens(user_email)
    if not tokens or "expires_at" not in tokens:
        return True
    try:
        return datetime.utcnow() > datetime.fromisoformat(tokens["expires_at"])
    except ValueError:
        return True


def get_instagram_credentials(user_email: str) -> Optional[dict]:
    """
    Get access token for use with Instagram Graph API.

    Args:
        user_email (str): User ID.

    Returns:
        dict or None: {"access_token": str} or None.
    """
    tokens = load_user_tokens(user_email)
    if not tokens or "access_token" not in tokens:
        return None
    return {"access_token": tokens["access_token"]}


def log_post(user_email: str, video_path: str, caption: str, drive_url: str = ""):
    """
    Append a post log entry.

    Args:
        user_email (str): User ID.
        video_path (str): Path to local MP4 file.
        caption (str): Reel caption.
        drive_url (str): Optional Google Drive share URL.
    """
    log_path = get_user_log_path(user_email)
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    log_entry = f"{datetime.utcnow().isoformat()} | {video_path} | {caption} | {drive_url or 'N/A'}\n"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(log_entry)

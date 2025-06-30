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


def get_user_token_path(username: str) -> str:
    return os.path.join(USER_DB_DIR, f"{username}.json")


def save_user_tokens(username: str, access_token: str, refresh_token: str, expires_in: int):
    path = get_user_token_path(username)
    data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_at": (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat()
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_user_tokens(username: str) -> Optional[dict]:
    path = get_user_token_path(username)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def update_access_token(username: str, new_token: str, new_expiry: int):
    tokens = load_user_tokens(username)
    if tokens:
        tokens["access_token"] = new_token
        tokens["expires_at"] = (datetime.utcnow() + timedelta(seconds=new_expiry)).isoformat()
        with open(get_user_token_path(username), "w", encoding="utf-8") as f:
            json.dump(tokens, f, indent=2)

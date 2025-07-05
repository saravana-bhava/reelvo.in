# File: utils/token_refresh.py

"""
Background daemon to refresh Instagram long-lived tokens.
Runs every 10 minutes, and refreshes token if it expires in under 5 minutes.
"""

import os
import time
import logging
import requests
from datetime import datetime, timedelta
from threading import Thread
from typing import List
from dotenv import load_dotenv
from utils.user_db import load_user_tokens, update_access_token

# Load environment variables
load_dotenv()

# Logging setup
logger = logging.getLogger("token_refresher")
logging.basicConfig(level=logging.INFO)

# Constants
CLIENT_ID = os.getenv("IG_CLIENT_ID")
CLIENT_SECRET = os.getenv("IG_CLIENT_SECRET")
REFRESH_URL = "https://graph.instagram.com/refresh_access_token"
REFRESH_INTERVAL = 600  # 10 minutes


def refresh_token_if_needed(user_name: str) -> None:
    """
    Refresh the Instagram access token for a user if it's expiring soon.

    Args:
        user_name: The user to refresh token for.
    """
    tokens = load_user_tokens(user_name)
    if not tokens:
        logger.warning(f"[⚠️] No tokens found for {user_name}")
        return

    try:
        expires_at_str = tokens.get("expires_at")
        refresh_token = tokens.get("refresh_token")
        if not expires_at_str or not refresh_token:
            logger.warning(f"[⚠️] Missing token data for {user_name}")
            return

        expires_at = datetime.fromisoformat(expires_at_str)

        # Skip if more than 5 minutes left
        if datetime.utcnow() + timedelta(minutes=5) < expires_at:
            logger.info(f"[✅] Token for {user_name} is still valid.")
            return

        logger.info(f"[🔄] Refreshing token for {user_name}...")

        response = requests.post(
            REFRESH_URL,
            params={
                "grant_type": "ig_refresh_token",
                "access_token": refresh_token
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        if "access_token" in data:
            update_access_token(
                user_name,
                new_access_token=data["access_token"],
                expires_in=data.get("expires_in", 3600)
            )
            logger.info(f"[✅] Token refreshed for {user_name}")
        else:
            logger.warning(f"[⚠️] Failed to refresh token for {user_name}: {data}")

    except Exception as e:
        logger.exception(f"[❌] Error refreshing token for {user_name}: {e}")


def token_refresh_daemon(user_names: List[str]) -> None:
    """
    Run a background loop that refreshes tokens for all users every 10 minutes.

    Args:
        user_names: List of user names whose tokens should be checked.
    """
    while True:
        logger.info("[🔁] Running token refresh daemon cycle...")
        for user_name in user_names:
            refresh_token_if_needed(user_name)
        time.sleep(REFRESH_INTERVAL)


def start_token_refresh_daemon(user_names: List[str]) -> None:
    """
    Start the token refresh process in a background daemon thread.

    Args:
        user_names: List of user names to monitor.
    """
    thread = Thread(target=token_refresh_daemon, args=(user_names,), daemon=True)
    thread.start()
    logger.info("[🧵] Token refresher thread started.")

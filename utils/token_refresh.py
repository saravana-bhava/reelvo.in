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
REFRESH_URL = "https://graph.instagram.com/refresh_access_token"
REFRESH_INTERVAL = 600  # 10 minutes


def refresh_token_if_needed(user_email: str) -> None:
    """
    Refresh the Instagram access token for a user if it's expiring soon.

    Args:
        user_email: The user to refresh token for.
    """
    tokens = load_user_tokens(user_email)
    if not tokens:
        logger.warning(f"[⚠️] No tokens found for {user_email}")
        return

    try:
        expires_at_str = tokens.get("expires_at")
        refresh_token = tokens.get("refresh_token")
        if not expires_at_str or not refresh_token:
            logger.warning(f"[⚠️] Missing token data for {user_email}")
            return

        expires_at = datetime.fromisoformat(expires_at_str)

        # Skip if more than 5 minutes remain
        if datetime.utcnow() + timedelta(minutes=5) < expires_at:
            logger.info(f"[✅] Token for {user_email} is still valid.")
            return

        logger.info(f"[🔄] Refreshing token for {user_email}...")

        response = requests.get(
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
                user_email=user_email,
                new_access_token=data["access_token"],
                expires_in=data.get("expires_in", 3600)
            )
            logger.info(f"[✅] Token refreshed for {user_email}")
        else:
            logger.warning(f"[⚠️] Token refresh failed for {user_email}: {data}")

    except Exception as e:
        logger.exception(f"[❌] Exception refreshing token for {user_email}: {e}")


def token_refresh_daemon(user_emails: List[str]) -> None:
    """
    Run a background loop that refreshes tokens for all users every 10 minutes.

    Args:
        user_emails: List of user emails whose tokens should be checked.
    """
    while True:
        logger.info("[🔁] Running token refresh cycle...")
        for user_email in user_emails:
            refresh_token_if_needed(user_email)
        time.sleep(REFRESH_INTERVAL)


def start_token_refresh_daemon(user_emails: List[str]) -> None:
    """
    Start the token refresh process in a background daemon thread.

    Args:
        user_emails: List of user emails to monitor.
    """
    thread = Thread(target=token_refresh_daemon, args=(user_emails,), daemon=True)
    thread.start()
    logger.info("[🧵] Token refresher daemon thread started.")

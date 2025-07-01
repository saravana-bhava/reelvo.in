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

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("token_refresher")

# Constants
CLIENT_ID = os.getenv("IG_CLIENT_ID")
CLIENT_SECRET = os.getenv("IG_CLIENT_SECRET")
REFRESH_INTERVAL = 600  # 10 minutes

REFRESH_URL = "https://graph.instagram.com/refresh_access_token"


def refresh_token_if_needed(username: str):
    """
    Refreshes the Instagram access token for a user if it's about to expire.
    """
    tokens = load_user_tokens(username)
    if not tokens:
        logger.warning(f"[⚠️] No tokens found for {username}")
        return

    try:
        expires_at = datetime.fromisoformat(tokens.get("expires_at"))
        refresh_token = tokens.get("refresh_token")

        if not refresh_token:
            logger.warning(f"[⚠️] No refresh token for {username}")
            return

        if datetime.utcnow() + timedelta(minutes=5) < expires_at:
            logger.info(f"[⏳] Token for {username} is still valid.")
            return  # Token not close to expiry yet

        logger.info(f"[🔄] Refreshing token for {username}...")

        response = requests.post(
            REFRESH_URL,
            params={
                "grant_type": "ig_refresh_token",
                "access_token": refresh_token
            },
            timeout=10
        )

        data = response.json()
        if "access_token" in data:
            update_access_token(username, data["access_token"], data.get("expires_in", 3600))
            logger.info(f"[✅] Token refreshed for {username}")
        else:
            logger.warning(f"[⚠️] Failed to refresh for {username}: {data}")

    except Exception as e:
        logger.exception(f"[❌] Error refreshing token for {username}: {e}")


def token_refresh_daemon(usernames: List[str]):
    """
    Continuously refreshes tokens for all given usernames every REFRESH_INTERVAL seconds.
    """
    while True:
        logger.info("[🔁] Running token refresh daemon...")
        for username in usernames:
            refresh_token_if_needed(username)
        time.sleep(REFRESH_INTERVAL)


def start_token_refresh_daemon(usernames: List[str]):
    """
    Starts the refresh loop in a background thread.
    """
    thread = Thread(target=token_refresh_daemon, args=(usernames,), daemon=True)
    thread.start()

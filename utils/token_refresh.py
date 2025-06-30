# File: utils/token_refresh.py

"""
Background daemon to refresh Instagram tokens using refresh_token.
Runs every 10 minutes and refreshes if <5 mins left on access token.
"""

import os
import time
import logging
import requests
from datetime import datetime, timedelta
from threading import Thread
from utils.user_db import load_user_tokens, update_access_token

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("token_refresher")

CLIENT_ID = os.getenv("IG_CLIENT_ID")
CLIENT_SECRET = os.getenv("IG_CLIENT_SECRET")
REFRESH_INTERVAL = 600  # every 10 minutes


def refresh_token_if_needed(username: str):
    tokens = load_user_tokens(username)
    if not tokens:
        return

    try:
        expires_at = datetime.fromisoformat(tokens["expires_at"])
        if datetime.utcnow() + timedelta(minutes=5) < expires_at:
            return

        refresh_token = tokens["refresh_token"]
        logger.info(f"[🔄] Refreshing token for {username}...")
        response = requests.post(
            "https://graph.instagram.com/refresh_access_token",
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


def token_refresh_daemon(usernames: list[str]):
    while True:
        logger.info("[🔁] Running token refresh daemon...")
        for user in usernames:
            refresh_token_if_needed(user)
        time.sleep(REFRESH_INTERVAL)


def start_token_refresh_daemon(usernames: list[str]):
    thread = Thread(target=token_refresh_daemon, args=(usernames,), daemon=True)
    thread.start()

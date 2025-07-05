# File: instagram_token_refresher.py

import os
import json
import time
import logging
import requests

# Setup
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_BASE = os.path.join(ROOT_DIR, "output")
logger = logging.getLogger("instagram_refresher")
logging.basicConfig(level=logging.INFO)


def refresh_instagram_tokens():
    """Refreshes Instagram long-lived tokens once every 24 hours for all users."""
    logger.info("🔄 Starting Instagram token refresher loop...")

    while True:
        users = [u for u in os.listdir(OUTPUT_BASE) if os.path.isdir(os.path.join(OUTPUT_BASE, u))]

        for user_email in users:
            tokens_path = os.path.join(OUTPUT_BASE, user_email, "tokens.json")
            if not os.path.exists(tokens_path):
                continue

            try:
                with open(tokens_path, "r", encoding="utf-8") as f:
                    tokens = json.load(f)

                token = tokens.get("long_lived_token")
                if not token or not isinstance(token, str):
                    logger.warning(f"[⚠️] No valid token for user: {user_email}")
                    continue

                refresh_url = (
                    "https://graph.instagram.com/refresh_access_token"
                    f"?grant_type=ig_refresh_token&access_token={token}"
                )

                logger.info(f"[🔁] Refreshing token for {user_email}...")
                response = requests.get(refresh_url, timeout=15)
                response.raise_for_status()

                data = response.json()
                tokens["long_lived_token"] = data.get("access_token", token)
                tokens["expires_in"] = data.get("expires_in")

                with open(tokens_path, "w", encoding="utf-8") as f:
                    json.dump(tokens, f, indent=2)

                logger.info(f"[✅] Token refreshed for {user_email} (expires in {tokens['expires_in']}s)")

            except Exception as e:
                logger.warning(f"[❌] Error refreshing token for {user_email}: {e}")

        logger.info("⏳ Sleeping for 24 hours...")
        time.sleep(24 * 3600)

# File: instagram_token_refresher.py

import os
import json
import time
import logging
import requests

OUTPUT_BASE = "output"
logger = logging.getLogger("reelvo")

def refresh_instagram_tokens():
    """Refreshes Instagram long-lived tokens every 24 hours for all users."""
    logger.info("🔄 Starting Instagram token refresher thread...")

    while True:
        for username in os.listdir(OUTPUT_BASE):
            user_dir = os.path.join(OUTPUT_BASE, username)
            tokens_path = os.path.join(user_dir, "tokens.json")

            if not os.path.exists(tokens_path):
                continue

            try:
                with open(tokens_path, "r") as f:
                    tokens = json.load(f)

                if "long_lived_token" not in tokens:
                    continue

                refresh_url = (
                    "https://graph.instagram.com/refresh_access_token"
                    f"?grant_type=ig_refresh_token&access_token={tokens['long_lived_token']}"
                )

                r = requests.get(refresh_url)
                if r.ok:
                    data = r.json()
                    tokens["long_lived_token"] = data.get("access_token", tokens["long_lived_token"])
                    tokens["expires_in"] = data.get("expires_in")

                    with open(tokens_path, "w") as f:
                        json.dump(tokens, f, indent=2)

                    logger.info(f"[✅] Refreshed token for {username}")

            except Exception as e:
                logger.warning(f"[❌] Token refresh error for {username}: {e}")

        time.sleep(24 * 3600)  # Run once per day

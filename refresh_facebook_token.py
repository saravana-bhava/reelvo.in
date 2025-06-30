# File: refresh_facebook_token.py

"""
Refreshes the Facebook long-lived access token and updates it in the .env file.
"""

import os
import requests
import logging
import shutil
from dotenv import load_dotenv

# Constants
ENV_PATH = ".env"
BACKUP_PATH = ".env.bak"

# Load environment variables
load_dotenv(ENV_PATH)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fb_token_refresh")

# Required environment variables
APP_ID = os.getenv("FB_APP_ID")
APP_SECRET = os.getenv("FB_APP_SECRET")
CURRENT_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN")


def validate_secrets() -> bool:
    """
    Ensure all required Facebook secrets are loaded.

    Returns:
        bool: True if valid, False otherwise.
    """
    if not all([APP_ID, APP_SECRET, CURRENT_TOKEN]):
        logger.error("❌ Missing FB_APP_ID, FB_APP_SECRET, or FB_PAGE_ACCESS_TOKEN in .env")
        return False
    return True


def refresh_long_lived_token() -> bool:
    """
    Refresh Facebook long-lived token and update .env.

    Returns:
        bool: True on success, False on failure.
    """
    if not validate_secrets():
        return False

    logger.info("🔄 Refreshing Facebook long-lived access token...")

    url = "https://graph.facebook.com/v19.0/oauth/access_token"
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": APP_ID,
        "client_secret": APP_SECRET,
        "fb_exchange_token": CURRENT_TOKEN
    }

    try:
        res = requests.get(url, params=params, timeout=10)
        res.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"[❌] Facebook API request failed: {e}")
        return False

    new_token = res.json().get("access_token")
    if not new_token:
        logger.error("[❌] No access_token in Facebook API response.")
        return False

    logger.info("✅ Token refreshed. Updating .env...")

    try:
        # Backup .env
        if os.path.exists(ENV_PATH):
            shutil.copyfile(ENV_PATH, BACKUP_PATH)

        # Read .env content
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Update or append token line
        with open(ENV_PATH, "w", encoding="utf-8") as f:
            updated = False
            for line in lines:
                if line.strip().startswith("FB_PAGE_ACCESS_TOKEN="):
                    f.write(f"FB_PAGE_ACCESS_TOKEN={new_token}\n")
                    updated = True
                else:
                    f.write(line)
            if not updated:
                f.write(f"\nFB_PAGE_ACCESS_TOKEN={new_token}\n")

        logger.info("✅ .env updated successfully. Backup saved as .env.bak")
        return True

    except Exception as e:
        logger.exception("[❌] Failed to update .env file")
        return False


if __name__ == "__main__":
    success = refresh_long_lived_token()
    exit(0 if success else 1)

# refresh_facebook_token.py

import os
import requests
import logging
import shutil
from dotenv import load_dotenv

# Config
ENV_PATH = ".env"
BACKUP_PATH = ".env.bak"

# Load .env
load_dotenv(ENV_PATH)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fb_token_refresh")

APP_ID = os.getenv("FB_APP_ID")
APP_SECRET = os.getenv("FB_APP_SECRET")
CURRENT_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN")


def validate_secrets():
    if not all([APP_ID, APP_SECRET, CURRENT_TOKEN]):
        logger.error("Missing FB_APP_ID, FB_APP_SECRET, or FB_PAGE_ACCESS_TOKEN in .env")
        return False
    return True


def refresh_long_lived_token():
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
        logger.error("[❌] No access_token in response")
        return False

    logger.info("✅ Token refreshed. Updating .env...")

    try:
        shutil.copyfile(ENV_PATH, BACKUP_PATH)
        with open(ENV_PATH, "r") as f:
            lines = f.readlines()

        with open(ENV_PATH, "w") as f:
            for line in lines:
                if line.startswith("FB_PAGE_ACCESS_TOKEN="):
                    f.write(f"FB_PAGE_ACCESS_TOKEN={new_token}\n")
                else:
                    f.write(line)

        logger.info("✅ .env updated. Backup saved as .env.bak")
        return True
    except Exception as e:
        logger.exception("[❌] Failed to update .env")
        return False


if __name__ == "__main__":
    success = refresh_long_lived_token()
    exit(0 if success else 1)

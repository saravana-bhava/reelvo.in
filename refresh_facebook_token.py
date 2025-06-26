import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

APP_ID = os.getenv("FB_APP_ID")
APP_SECRET = os.getenv("FB_APP_SECRET")
CURRENT_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN")
ENV_PATH = ".env"

def refresh_long_lived_token():
    print("🔄 Refreshing Facebook long-lived access token...")
    url = f"https://graph.facebook.com/v19.0/oauth/access_token"
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": APP_ID,
        "client_secret": APP_SECRET,
        "fb_exchange_token": CURRENT_TOKEN
    }

    res = requests.get(url, params=params)
    if res.status_code != 200:
        print(f"[❌] Refresh failed: {res.text}")
        return

    new_token = res.json().get("access_token")
    if not new_token:
        print("[❌] No access_token in response")
        return

    print("✅ Token refreshed. Updating .env...")

    # Update .env file
    with open(ENV_PATH, "r") as f:
        lines = f.readlines()

    with open(ENV_PATH, "w") as f:
        for line in lines:
            if line.startswith("FB_PAGE_ACCESS_TOKEN="):
                f.write(f"FB_PAGE_ACCESS_TOKEN={new_token}\n")
            else:
                f.write(line)

    print("✅ .env updated with new token.")

if __name__ == "__main__":
    refresh_long_lived_token()

import os
import json

ACCOUNTS_FILE = "db/user_accounts.json"
HISTORY_FILE = "db/reel_history.json"

os.makedirs("db", exist_ok=True)
for file in [ACCOUNTS_FILE, HISTORY_FILE]:
    if not os.path.exists(file):
        with open(file, "w") as f:
            f.write("{}")

def save_instagram_credentials(username, access_token, ig_account_id):
    with open(ACCOUNTS_FILE, "r+", encoding="utf-8") as f:
        data = json.load(f)
        data[username] = {
            "access_token": access_token,
            "ig_account_id": ig_account_id
        }
        f.seek(0)
        json.dump(data, f, indent=2)
        f.truncate()

def get_instagram_credentials(username):
    with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f).get(username)

def log_post(username, category, permalink):
    from datetime import datetime
    with open(HISTORY_FILE, "r+", encoding="utf-8") as f:
        data = json.load(f)
        if username not in data:
            data[username] = []
        data[username].append({
            "category": category,
            "permalink": permalink,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
        f.seek(0)
        json.dump(data, f, indent=2)
        f.truncate()

# File: utils/gofile.py

import os
import sys
import logging
import requests
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gofile")

GOFILE_ACCOUNT_TOKEN = os.getenv("GOFILE_ACCOUNT_TOKEN")
GOFILE_PARENT_FOLDER_ID = os.getenv("GOFILE_PARENT_FOLDER_ID")

API_BASE = "https://api.gofile.io"

def get_or_create_user_folder(email: str) -> str | None:
    headers = {
        "Authorization": f"Bearer {GOFILE_ACCOUNT_TOKEN}"
    }
    data = {
        "parentFolderId": GOFILE_PARENT_FOLDER_ID,
        "folderName": email
    }

    response = requests.post(f"{API_BASE}/contents/createFolder", json=data, headers=headers)
    if response.status_code != 200:
        logger.error(f"[❌] Failed to create/find folder: {response.status_code} - {response.text}")
        return None

    try:
        result = response.json()
        if result["status"] != "ok":
            logger.error(f"[❌] createFolder error: {result}")
            return None
        folder_id = result["data"]["id"]
        logger.info(f"[📁] Folder ID for {email}: {folder_id}")
        return folder_id
    except Exception as e:
        logger.exception("[❌] Failed to parse createFolder response")
        return None

def upload_to_gofile(file_path: str, email: str) -> str | None:
    logger.info(f"[📤] Uploading: {file_path}")

    folder_id = get_or_create_user_folder(email)
    if not folder_id:
        return None

    headers = {
        "Authorization": f"Bearer {GOFILE_ACCOUNT_TOKEN}"
    }

    with open(file_path, "rb") as f:
        files = {"file": f}
        data = {"folderId": folder_id}
        response = requests.post("https://upload.gofile.io/uploadfile", files=files, headers=headers, data=data)

    if response.status_code != 200:
        logger.error(f"[❌] Upload failed: {response.status_code} - {response.text}")
        return None

    try:
        result = response.json()
        logger.info(f"[🧾] Raw response: {result}")
        if result["status"] != "ok":
            logger.error(f"[❌] Upload error: {result}")
            return None

        file_data = result["data"]
        server = file_data["servers"][0]
        file_id = file_data["id"]
        file_name = file_data["name"]

        direct_link = f"https://{server}.gofile.io/download/web/{file_id}/{file_name}"
        logger.info(f"[🔗] Direct download link: {direct_link}")
        return direct_link
    except Exception as e:
        logger.exception("[❌] Failed to parse upload response")
        return None

def download_from_gofile(url: str, output_path: str, account_token: str):
    print(url)
    print(output_path)
    print(account_token)
    headers = {
        "Referer": "https://gofile.io/",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
    }
    cookies = {
        "accountToken": account_token
    }

    logger.info(f"[⬇️] Downloading from: {url}")
    try:
        response = requests.get(url, headers=headers, cookies=cookies, stream=True)
        response.raise_for_status()

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        logger.info(f"[✅] Download completed: {output_path}")
    except requests.exceptions.RequestException as e:
        logger.error(f"[❌] Download failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python utils/gofile.py <file_path> <user_email>")
        sys.exit(1)

    file_path = sys.argv[1]
    user_email = sys.argv[2]

    direct_url = upload_to_gofile(file_path, user_email)
    if direct_url and GOFILE_ACCOUNT_TOKEN:
        file_name = os.path.basename(direct_url)
        local_download_path = os.path.join("downloads", user_email, file_name)
        download_from_gofile(direct_url, local_download_path, GOFILE_ACCOUNT_TOKEN)
        print(f"[🔗] {direct_url}")
    else:
        logger.error("[⚠️] Upload or download skipped due to missing token or link.")

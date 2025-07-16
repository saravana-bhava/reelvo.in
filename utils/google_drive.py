# File: utils/google_drive.py

"""
Google Drive integration using OAuth.
- Uploads videos to authenticated user's Drive.
- Public sharing via link.
"""

import os
import mimetypes
import logging
from typing import Optional, Tuple

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Logging
logger = logging.getLogger("google_drive")
logging.basicConfig(level=logging.INFO)

# OAuth config
SCOPES = ["https://www.googleapis.com/auth/drive.file"]
CREDENTIALS_PATH = os.getenv("GOOGLE_OAUTH_CREDENTIALS", "credentials.json")
TOKEN_PATH = "token.json"

# Optional: UI progress support
try:
    from utils.progress_tracker import update_progress
except ImportError:
    def update_progress(task_id, status, percent): pass


def get_drive_service():
    """Authenticate via OAuth and return a Drive service instance."""
    creds = None

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w") as token:
            token.write(creds.to_json())
            logger.info("[✅] Saved new OAuth token.")

    logger.info("[🔐] Google Drive authenticated.")
    return build("drive", "v3", credentials=creds)


def upload_to_google_drive(
    local_path: str,
    user_name: str,
    task_id: Optional[str] = None
) -> Tuple[Optional[str], Optional[str]]:
    """
    Uploads a video to the authenticated user's Drive.

    Returns:
        (public_url, error_message)
    """
    if not os.path.exists(local_path):
        return None, "[❌] File does not exist."

    try:
        update_progress(task_id, "📁 Connecting to Google Drive...", 80)
        service = get_drive_service()

        filename = os.path.basename(local_path)
        mime_type = mimetypes.guess_type(local_path)[0] or "video/mp4"
        media = MediaFileUpload(local_path, mimetype=mime_type, resumable=True)

        update_progress(task_id, f"⏫ Uploading {filename}...", 85)
        logger.info(f"[📤] Uploading file: {filename}")

        uploaded = service.files().create(
            body={"name": filename},
            media_body=media,
            fields="id"
        ).execute()

        file_id = uploaded.get("id")
        if not file_id:
            return None, "[❌] Upload succeeded but no file ID returned."

        logger.info("[🔓] Making file public...")
        service.permissions().create(
            fileId=file_id,
            body={"type": "anyone", "role": "reader"},
            fields="id"
        ).execute()

        public_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        update_progress(task_id, "✅ Upload complete", 90)
        logger.info(f"[✅] File URL: {public_url}")
        return public_url, None

    except Exception as e:
        logger.exception("[❌] Google Drive upload failed.")
        return None, f"[❌] Upload failed: {str(e)}"


# CLI test
if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python utils/google_drive.py <local_path> <user_name>")
        sys.exit(1)

    path = sys.argv[1]
    user = sys.argv[2]

    url, error = upload_to_google_drive(path, user)
    if error:
        logger.error(error)
    else:
        print(f"✅ {url}")

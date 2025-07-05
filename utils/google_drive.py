# File: utils/google_drive.py

"""
Google Drive integration for uploading videos under user-specific folders.
Includes:
- Service account auth
- Automatic folder creation per user
- Public sharing via URL
"""

import os
import mimetypes
import logging
from typing import Optional, Tuple
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Load .env
load_dotenv()

# Logging
logger = logging.getLogger("google_drive")
logging.basicConfig(level=logging.INFO)

# Constants
SCOPES = ["https://www.googleapis.com/auth/drive"]
FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"
GDRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_PARENT_FOLDER_ID")
GDRIVE_CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "secure/credentials.json")

# Optional: UI progress support
try:
    from progress import update_progress
except ImportError:
    def update_progress(task_id, status, percent): pass


def get_drive_service():
    """Initialize and return Google Drive service."""
    if not os.path.exists(GDRIVE_CREDENTIALS_PATH):
        raise FileNotFoundError(f"[❌] Missing credentials: {GDRIVE_CREDENTIALS_PATH}")

    creds = service_account.Credentials.from_service_account_file(
        GDRIVE_CREDENTIALS_PATH, scopes=SCOPES
    )
    logger.info("[🔐] Google Drive authenticated.")
    return build("drive", "v3", credentials=creds)


def get_or_create_user_folder(service, user_name: str) -> str:
    """
    Get or create a folder for the user under the parent folder.

    Returns:
        str: Google Drive folder ID
    """
    if not GDRIVE_FOLDER_ID:
        raise EnvironmentError("[❌] Missing GOOGLE_DRIVE_PARENT_FOLDER_ID in .env")

    logger.info(f"[📁] Locating folder for user: {user_name}")

    query = (
        f"'{GDRIVE_FOLDER_ID}' in parents and name = '{user_name}' "
        f"and mimeType = '{FOLDER_MIME_TYPE}' and trashed = false"
    )
    result = service.files().list(q=query, fields="files(id)").execute()
    folders = result.get("files", [])

    if folders:
        folder_id = folders[0]["id"]
        logger.info(f"[✅] Found folder ID: {folder_id}")
        return folder_id

    logger.info(f"[📂] Creating folder for user: {user_name}")
    metadata = {
        "name": user_name,
        "mimeType": FOLDER_MIME_TYPE,
        "parents": [GDRIVE_FOLDER_ID]
    }
    folder = service.files().create(body=metadata, fields="id").execute()
    folder_id = folder["id"]
    logger.info(f"[✅] Created folder ID: {folder_id}")
    return folder_id


def upload_to_google_drive(
    local_path: str,
    user_name: str,
    task_id: Optional[str] = None
) -> Tuple[Optional[str], Optional[str]]:
    """
    Uploads a video to Google Drive and returns a shareable public URL.

    Returns:
        (public_url, error_message)
    """
    if not os.path.exists(local_path):
        return None, "[❌] File does not exist."

    try:
        update_progress(task_id, "📁 Connecting to Google Drive...", 80)
        service = get_drive_service()

        update_progress(task_id, "📂 Preparing folder...", 82)
        folder_id = get_or_create_user_folder(service, user_name)

        filename = os.path.basename(local_path)
        mime_type = mimetypes.guess_type(local_path)[0] or "video/mp4"
        media = MediaFileUpload(local_path, mimetype=mime_type, resumable=True)

        update_progress(task_id, f"⏫ Uploading {filename}...", 85)
        logger.info(f"[📤] Uploading file: {filename}")

        uploaded = service.files().create(
            body={"name": filename, "parents": [folder_id]},
            media_body=media,
            fields="id"
        ).execute()

        file_id = uploaded.get("id")
        if not file_id:
            return None, "[❌] Upload succeeded but no file ID returned."

        logger.info("[🔓] Setting file to public...")
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
        return None, f"[❌] Google Drive upload failed: {str(e)}"


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

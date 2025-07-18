# File: utils/google_drive.py

"""
Google Drive integration using OAuth or Service Account.
- Uploads videos to a single Google account or service account.
- All files go inside: reels/<user_email>/ inside Shared Drive if configured.
- Public sharing via download link.
"""

import os
import mimetypes
import logging
from typing import Optional, Tuple
from google.oauth2.credentials import Credentials
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Logging
logger = logging.getLogger("google_drive")
logging.basicConfig(level=logging.INFO)

# Configuration
SCOPES = ["https://www.googleapis.com/auth/drive.file"]
CREDENTIALS_PATH = os.getenv("GOOGLE_OAUTH_CREDENTIALS", "credentials.json")
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "credentials.json")
USE_SERVICE_ACCOUNT = os.getenv("USE_SERVICE_ACCOUNT", "false").lower() == "true"
TOKEN_PATH = "token.json"
PARENT_SHARED_FOLDER_ID = os.getenv("GOOGLE_DRIVE_PARENT_FOLDER_ID")
USE_SHARED_DRIVE = os.getenv("GOOGLE_USE_SHARED_DRIVE", "false").lower() == "true"

# Optional: UI progress tracker
try:
    from utils.progress_tracker import update_progress
except ImportError:
    def update_progress(task_id, status, percent): pass


def get_drive_service():
    """Return a Google Drive service client using either OAuth or Service Account."""
    if USE_SERVICE_ACCOUNT:
        if not os.path.exists(SERVICE_ACCOUNT_FILE):
            raise FileNotFoundError(f"Missing service account file: {SERVICE_ACCOUNT_FILE}")
        creds = ServiceAccountCredentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        logger.info("[🔐] Using service account for Google Drive.")
    else:
        creds = None
        if os.path.exists(TOKEN_PATH):
            creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

        if not creds or not creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
            with open(TOKEN_PATH, "w") as token:
                token.write(creds.to_json())
                logger.info("[✅] Saved new OAuth token.")

        logger.info("[🔐] Using OAuth for Google Drive.")

    return build("drive", "v3", credentials=creds)


def get_or_create_folder(service, name: str, parent_id: Optional[str] = None) -> str:
    """Return folder ID for given name under parent, or create if missing."""
    query = f"name = '{name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    if parent_id:
        query += f" and '{parent_id}' in parents"

    result = service.files().list(
        q=query,
        spaces="drive",
        fields="files(id, name)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True
    ).execute()

    folders = result.get("files", [])
    if folders:
        return folders[0]["id"]

    metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder"
    }
    if parent_id:
        metadata["parents"] = [parent_id]

    folder = service.files().create(
        body=metadata,
        fields="id",
        supportsAllDrives=True
    ).execute()

    return folder["id"]


def upload_to_google_drive(
    local_path: str,
    user_name: str,
    task_id: Optional[str] = None
) -> Tuple[Optional[str], Optional[str]]:
    """
    Uploads a video to the user's folder under 'reels' in Google Drive.

    Returns:
        (public_url, error_message)
    """
    if not os.path.exists(local_path):
        return None, "[❌] File does not exist."

    try:
        update_progress(task_id, "📁 Connecting to Google Drive...", 83)
        service = get_drive_service()

        if not PARENT_SHARED_FOLDER_ID:
            return None, "[❌] Missing GOOGLE_DRIVE_PARENT_FOLDER_ID in .env."

        # Folder hierarchy: reels (shared) → user
        reels_folder_id = PARENT_SHARED_FOLDER_ID
        user_folder_id = get_or_create_folder(service, user_name, reels_folder_id)

        filename = os.path.basename(local_path)
        mime_type = mimetypes.guess_type(local_path)[0] or "video/mp4"
        media = MediaFileUpload(local_path, mimetype=mime_type, resumable=True)

        update_progress(task_id, f"⏫ Uploading {filename}...", 86)
        logger.info(f"[📤] Uploading file: {filename}")

        uploaded = service.files().create(
            body={
                "name": filename,
                "parents": [user_folder_id]
            },
            media_body=media,
            fields="id",
            supportsAllDrives=True
        ).execute()

        file_id = uploaded.get("id")
        if not file_id:
            return None, "[❌] Upload succeeded but no file ID returned."

        logger.info("[🔓] Making file public...")
        service.permissions().create(
            fileId=file_id,
            body={"type": "anyone", "role": "reader"},
            fields="id",
            supportsAllDrives=True
        ).execute()

        public_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        update_progress(task_id, "✅ Upload complete", 95)
        logger.info(f"[✅] File URL: {public_url}")
        return public_url, None

    except Exception as e:
        logger.exception("[❌] Google Drive upload failed.")
        return None, f"[❌] Upload failed: {str(e)}"


# CLI test
if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python utils/google_drive.py <local_path> <user_email>")
        sys.exit(1)

    path = sys.argv[1]
    user = sys.argv[2]

    url, error = upload_to_google_drive(path, user)
    if error:
        logger.error(error)
    else:
        print(f"✅ {url}")

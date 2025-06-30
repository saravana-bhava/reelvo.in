# File: utils/google_drive.py

"""
Google Drive integration for uploading videos under user-specific folders.
Includes:
- Service account auth
- Automatic folder creation
- Public sharing via link
"""

import os
import mimetypes
import logging
from typing import Optional, Tuple
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Load environment variables
load_dotenv()

# Logging setup
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
        raise FileNotFoundError(f"[❌] Missing Google service account file: {GDRIVE_CREDENTIALS_PATH}")

    creds = service_account.Credentials.from_service_account_file(
        GDRIVE_CREDENTIALS_PATH, scopes=SCOPES
    )
    logger.info("[🔑] Authenticated with Google Drive.")
    return build("drive", "v3", credentials=creds)


def get_or_create_user_folder(service, username: str) -> str:
    """
    Get or create folder for the user in Drive.

    Args:
        service: Google Drive API service object.
        username (str): Folder name (user).

    Returns:
        str: Folder ID.
    """
    if not GDRIVE_FOLDER_ID:
        raise EnvironmentError("[❌] GOOGLE_DRIVE_PARENT_FOLDER_ID not set in .env")

    logger.info(f"[📁] Checking folder for user: {username}")
    query = (
        f"'{GDRIVE_FOLDER_ID}' in parents and name = '{username}' "
        f"and mimeType = '{FOLDER_MIME_TYPE}' and trashed = false"
    )
    results = service.files().list(q=query, fields="files(id)").execute()
    folders = results.get("files", [])

    if folders:
        folder_id = folders[0]["id"]
        logger.info(f"[✅] Found existing folder ID: {folder_id}")
        return folder_id

    logger.info(f"[📂] Creating new folder for user: {username}")
    folder_metadata = {
        "name": username,
        "mimeType": FOLDER_MIME_TYPE,
        "parents": [GDRIVE_FOLDER_ID]
    }
    folder = service.files().create(body=folder_metadata, fields="id").execute()
    logger.info(f"[✅] Folder created with ID: {folder['id']}")
    return folder["id"]


def upload_to_google_drive(
    local_path: str,
    username: str,
    task_id: Optional[str] = None
) -> Tuple[Optional[str], Optional[str]]:
    """
    Upload a local file to Google Drive and return the public URL or error.

    Args:
        local_path (str): Path to local file.
        username (str): User folder name.
        task_id (str): Optional task ID for UI progress.

    Returns:
        Tuple[str | None, str | None]: (public_url, error_message)
    """
    if not os.path.exists(local_path):
        return None, "[❌] File not found."

    try:
        update_progress(task_id, "📁 Connecting to Google Drive...", 80)
        service = get_drive_service()

        update_progress(task_id, "📂 Preparing user folder...", 82)
        folder_id = get_or_create_user_folder(service, username)

        file_metadata = {
            "name": os.path.basename(local_path),
            "parents": [folder_id]
        }

        mime_type = mimetypes.guess_type(local_path)[0] or "video/mp4"
        media = MediaFileUpload(local_path, mimetype=mime_type, resumable=True)

        update_progress(task_id, "⏫ Uploading video to Drive...", 85)
        logger.info(f"[📤] Uploading file: {local_path}")
        uploaded = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id"
        ).execute()

        logger.info("[🔓] Making uploaded file public...")
        service.permissions().create(
            fileId=uploaded["id"],
            body={"role": "reader", "type": "anyone"},
            fields="id"
        ).execute()

        file_id = uploaded["id"]
        public_url = f"https://drive.google.com/file/d/{file_id}/view"
        update_progress(task_id, "✅ Upload complete", 90)

        logger.info(f"[✅] File available at: {public_url}")
        return public_url, None

    except Exception as e:
        logger.exception("[❌] Google Drive upload failed.")
        return None, f"[❌] Google Drive upload failed: {str(e)}"


# CLI usage for testing
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python utils/google_drive.py <local_path> <username>")
        sys.exit(1)

    path, user = sys.argv[1], sys.argv[2]
    url, error = upload_to_google_drive(path, user)
    if error:
        logger.error(error)
    else:
        print(url)

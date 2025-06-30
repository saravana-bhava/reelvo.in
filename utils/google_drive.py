# File: utils/google_drive.py

"""
Google Drive integration for uploading videos under user-specific folders.
Includes support for:
- Service account auth
- Automatic folder creation
- Public sharing
"""

import os
import mimetypes
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Load environment
load_dotenv()

# Constants
SCOPES = ["https://www.googleapis.com/auth/drive"]
FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"
GDRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_PARENT_FOLDER_ID")
GDRIVE_CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "secure/credentials.json")

# Optional: UI progress hook
try:
    from progress import update_progress
except ImportError:
    def update_progress(task_id, status, percent): pass


def get_drive_service():
    """Initialize and return Google Drive service instance."""
    creds = service_account.Credentials.from_service_account_file(
        GDRIVE_CREDENTIALS_PATH, scopes=SCOPES
    )
    return build("drive", "v3", credentials=creds)


def get_or_create_user_folder(service, username: str) -> str:
    """
    Return folder ID for a user's folder under the parent.
    Creates the folder if it doesn't exist.
    """
    if not GDRIVE_FOLDER_ID:
        raise ValueError("[❌] GOOGLE_DRIVE_PARENT_FOLDER_ID not set in .env")

    query = (
        f"'{GDRIVE_FOLDER_ID}' in parents and name = '{username}' "
        f"and mimeType = '{FOLDER_MIME_TYPE}' and trashed = false"
    )
    results = service.files().list(q=query, fields="files(id)").execute()
    folders = results.get("files", [])
    if folders:
        return folders[0]["id"]

    folder_metadata = {
        "name": username,
        "mimeType": FOLDER_MIME_TYPE,
        "parents": [GDRIVE_FOLDER_ID]
    }
    folder = service.files().create(body=folder_metadata, fields="id").execute()
    return folder["id"]


def upload_to_google_drive(local_path: str, username: str, task_id: str = None) -> tuple[str | None, str | None]:
    """
    Upload a file to Google Drive under the specified user's folder.
    Returns: (public_download_url, error_message)
    """
    try:
        if not os.path.exists(local_path):
            return None, "[❌] File not found."

        update_progress(task_id, "📁 Connecting to Google Drive...", 80)
        service = get_drive_service()

        update_progress(task_id, "📂 Preparing user folder...", 82)
        folder_id = get_or_create_user_folder(service, username)

        file_metadata = {
            "name": os.path.basename(local_path),
            "parents": [folder_id]
        }

        mime_type = mimetypes.guess_type(local_path)[0] or "video/mp4"
        media = MediaFileUpload(local_path, resumable=True, mimetype=mime_type)

        update_progress(task_id, "⏫ Uploading video to Drive...", 85)
        uploaded = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id"
        ).execute()

        # Make file public
        service.permissions().create(
            fileId=uploaded["id"],
            body={"role": "reader", "type": "anyone"},
            fields="id"
        ).execute()

        file_id = uploaded["id"]
        public_url = f"https://drive.google.com/file/d/{file_id}/view"

        update_progress(task_id, "✅ Upload complete", 90)
        return public_url, None

    except Exception as e:
        return None, f"[❌] Google Drive upload failed: {str(e)}"


# CLI usage
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python utils/google_drive.py <local_path> <username>")
        sys.exit(1)

    local_path, username = sys.argv[1], sys.argv[2]
    url, error = upload_to_google_drive(local_path, username)
    print(error if error else url)

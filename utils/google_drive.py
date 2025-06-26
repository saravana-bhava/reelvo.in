import os
import mimetypes
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
SCOPES = ["https://www.googleapis.com/auth/drive"]
FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"
GDRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_PARENT_FOLDER_ID")
GDRIVE_CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "secure/credentials.json")

def get_drive_service():
    creds = service_account.Credentials.from_service_account_file(
        GDRIVE_CREDENTIALS_PATH,
        scopes=SCOPES
    )
    return build("drive", "v3", credentials=creds)

def get_or_create_user_folder(service, username):
    """Returns Drive folder ID for user. Creates one if not found."""
    if not GDRIVE_FOLDER_ID:
        raise ValueError("[❌] GOOGLE_DRIVE_PARENT_FOLDER_ID is not set in .env")

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

def upload_to_google_drive(local_path, username):
    try:
        if not os.path.exists(local_path):
            return None, "[❌] Local file missing."

        service = get_drive_service()
        user_folder_id = get_or_create_user_folder(service, username)

        file_metadata = {
            "name": os.path.basename(local_path),
            "parents": [user_folder_id]
        }

        mime_type = mimetypes.guess_type(local_path)[0] or "video/mp4"
        media = MediaFileUpload(local_path, resumable=True, mimetype=mime_type)

        uploaded = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id"
        ).execute()

        service.permissions().create(
            fileId=uploaded["id"],
            body={"role": "reader", "type": "anyone"},
            fields="id"
        ).execute()

        file_id = uploaded["id"]
        public_url = f"https://drive.google.com/uc?id={file_id}&export=download"
        return public_url, None

    except Exception as e:
        return None, f"[❌] Google Drive upload failed: {str(e)}"

# CLI usage
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python utils/google_drive.py <local_path> <username>")
    else:
        local_path, username = sys.argv[1], sys.argv[2]
        url, err = upload_to_google_drive(local_path, username)
        print(err or url)

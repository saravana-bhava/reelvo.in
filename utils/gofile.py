# File: utils/gofile.py

"""
GoFile.io integration for temporary video hosting.
- Uploads videos via GoFile's API.
- Returns a public download URL.
"""

import os
import requests
import logging
from typing import Optional, Tuple
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Logging
logger = logging.getLogger("gofile")
logging.basicConfig(level=logging.INFO)

# Optional: UI progress tracker
try:
    from utils.progress_tracker import update_progress
except ImportError:
    def update_progress(task_id, status, percent): pass


def upload_to_gofile(
    local_path: str,
    user_name: str,
    task_id: Optional[str] = None
) -> Tuple[Optional[str], Optional[str]]:
    """
    Uploads a video to GoFile.io and returns a public download URL.

    Returns:
        (public_url, error_message)
    """
    if not os.path.exists(local_path):
        return None, "[❌] File does not exist."

    try:
        update_progress(task_id, "📁 Connecting to GoFile.io...", 83)
        logger.info(f"[📤] Uploading: {local_path}")

        # Step 1: Get the best upload server
        server_resp = requests.get("https://api.gofile.io/getServer").json()
        server = server_resp["data"]["server"]
        logger.info(f"[🔌] Upload server: {server}")

        update_progress(task_id, "⏫ Uploading video...", 88)
        with open(local_path, 'rb') as f:
            upload_resp = requests.post(
                f"https://{server}.gofile.io/uploadFile",
                files={"file": f}
            ).json()

        if upload_resp["status"] != "ok":
            return None, "[❌] Upload failed."

        public_url = upload_resp["data"]["downloadPage"]
        update_progress(task_id, "✅ Upload complete", 95)
        logger.info(f"[✅] Uploaded URL: {public_url}")
        return public_url, None

    except Exception as e:
        logger.exception("[❌] GoFile upload failed.")
        return None, f"[❌] Upload failed: {str(e)}"


# CLI test
if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python utils/gofile.py <local_path> <user_name>")
        sys.exit(1)

    path = sys.argv[1]
    user = sys.argv[2]

    url, error = upload_to_gofile(path, user)
    if error:
        print(error, file=sys.stderr)
    else:
        print(f"✅ {url}")

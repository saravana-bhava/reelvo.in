# File: utils/insta_direct.py

"""
Automated posting of Instagram Reels via Graph API.
Handles:
- Google Drive upload (if needed)
- IG reel container creation
- Polling for media readiness
- Publishing + permalink fetch
- Logging to history
"""

import os
import time
import logging
import requests
from typing import Optional
from utils.google_drive import upload_to_google_drive
from utils.user_db import get_instagram_credentials, log_post

# Setup logger
logger = logging.getLogger("instagram")
logging.basicConfig(level=logging.INFO)

# Optional progress status tracker
try:
    from progress import update_progress
except ImportError:
    def update_progress(task_id, status, percent): pass


def post_to_instagram_direct(
    video_path: str,
    caption: str,
    ig_account_id: Optional[str] = None,
    access_token: Optional[str] = None,
    username: str = "default",
    video_url: Optional[str] = None,
    task_id: Optional[str] = None
) -> str:
    """
    Uploads and posts an Instagram Reel using the Graph API.

    Returns:
        str: Success/failure message with permalink or error.
    """
    try:
        update_progress(task_id, "📤 Preparing Instagram upload...", 91)
        logger.info(f"[🚀] Posting reel for user: {username}")

        # Fetch credentials if not provided
        if not access_token or not ig_account_id:
            creds = get_instagram_credentials(username)
            if not creds:
                return "[❌] Instagram account not linked for this user."
            access_token = creds.get("access_token")
            ig_account_id = creds.get("ig_account_id")

        if not video_url:
            update_progress(task_id, "📁 Uploading to Google Drive...", 92)
            video_url, upload_error = upload_to_google_drive(video_path, username, task_id)
            if not video_url:
                return f"[❌] Failed to upload video to Google Drive: {upload_error}"

        logger.info(f"[🎬] Submitting reel to Graph API with video URL: {video_url}")
        update_progress(task_id, "📤 Uploading reel to Instagram...", 94)
        container_res = requests.post(
            f"https://graph.facebook.com/v19.0/{ig_account_id}/media",
            params={
                "media_type": "REELS",
                "video_url": video_url,
                "caption": caption,
                "access_token": access_token,
                "share_to_feed": "true"
            }
        )

        if container_res.status_code != 200:
            logger.error(f"[❌] Container upload failed: {container_res.text}")
            return f"[❌] Container upload failed ({container_res.status_code}): {container_res.text}"

        container_id = container_res.json().get("id")
        if not container_id:
            return "[❌] No container ID returned by Graph API."

        update_progress(task_id, "⏳ Waiting for media processing...", 95)
        logger.info(f"[⏳] Polling status for container: {container_id}")

        # Poll for media readiness (max 60s)
        for _ in range(12):
            time.sleep(5)
            status_res = requests.get(
                f"https://graph.facebook.com/v19.0/{container_id}",
                params={
                    "fields": "status_code",
                    "access_token": access_token
                }
            )
            if status_res.status_code == 200:
                status = status_res.json().get("status_code")
                logger.info(f"[ℹ️] Status code: {status}")
                if status == "FINISHED":
                    update_progress(task_id, "✅ Media ready. Publishing...", 96)
                    break
            else:
                return f"[❌] Failed to poll status ({status_res.status_code}): {status_res.text}"
        else:
            return "[❌] Media not ready after 60 seconds of polling."

        # Publish the reel
        publish_res = requests.post(
            f"https://graph.facebook.com/v19.0/{ig_account_id}/media_publish",
            params={
                "creation_id": container_id,
                "access_token": access_token
            }
        )

        if publish_res.status_code != 200:
            return f"[❌] Publishing failed ({publish_res.status_code}): {publish_res.text}"

        post_id = publish_res.json().get("id")
        if not post_id:
            return "[❌] Publishing succeeded but no post ID returned."

        # Fetch permalink
        permalink_res = requests.get(
            f"https://graph.facebook.com/v19.0/{post_id}",
            params={
                "fields": "permalink",
                "access_token": access_token
            }
        )

        if permalink_res.status_code == 200:
            permalink = permalink_res.json().get("permalink")
            if permalink:
                update_progress(task_id, "🎉 Reel published!", 100)

                # 📝 Log this post
                category = os.path.splitext(os.path.basename(video_path))[0]
                log_post(username, category, permalink)

                logger.info(f"[✅] Reel published → {permalink}")
                return f"[✅] Reel posted: <a href='{permalink}' target='_blank'>{permalink}</a>"
            else:
                return "[✅] Reel posted but no permalink returned."

        return f"[✅] Reel posted (ID: {post_id}), but failed to fetch permalink."

    except Exception as e:
        logger.exception("[❌] Exception during Instagram post.")
        return f"[❌] Unexpected exception during Instagram upload: {str(e)}"

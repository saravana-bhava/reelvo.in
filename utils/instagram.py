# File: utils/instagram.py

import os
import json
import time
import requests
from urllib.parse import urlencode
from utils.user_db import get_instagram_credentials, log_post

INSTAGRAM_API_URL = "https://graph.facebook.com/v19.0"

def post_to_instagram(video_path: str, caption: str, username: str, video_url: str = "", task_id: str = None) -> str:
    """
    Uploads a reel to Instagram for a given user.
    """
    creds = get_instagram_credentials(username)
    if not creds:
        return "❌ No Instagram credentials found for user."

    access_token = creds.get("access_token")
    if not access_token:
        return "❌ Access token missing."

    try:
        # Step 1: Upload video container to Instagram (reel publishing endpoint)
        container_url = f"{INSTAGRAM_API_URL}/{creds.get('user_id', '')}/media"
        payload = {
            "video_url": video_url or "",  # This can be replaced with direct upload if needed
            "media_type": "REELS",
            "caption": caption,
            "access_token": access_token,
            "share_to_feed": "true",
        }

        if not video_url:
            # For direct file upload, you'd need to upload to a publicly accessible URL or use FB Resumable Upload API
            return "❌ Missing video_url for Instagram upload (direct uploads not supported via Graph API without FB page)."

        r1 = requests.post(container_url, data=payload)
        r1.raise_for_status()
        container_id = r1.json().get("id")

        if not container_id:
            return "❌ Failed to create IG container."

        # Step 2: Publish the container
        publish_url = f"{INSTAGRAM_API_URL}/{creds.get('user_id', '')}/media_publish"
        r2 = requests.post(publish_url, data={
            "creation_id": container_id,
            "access_token": access_token
        })
        r2.raise_for_status()

        # Optional: Get permalink or confirmation
        result = r2.json()
        media_id = result.get("id")

        if media_id:
            time.sleep(3)  # Give some time for the media to appear
            r3 = requests.get(
                f"{INSTAGRAM_API_URL}/{media_id}",
                params={"fields": "permalink", "access_token": access_token}
            )
            permalink = r3.json().get("permalink", "URL not available")

            # 📝 Log this post
            log_post(username, video_path=video_path, caption=caption, drive_url=permalink)

            return f"📤 Reel posted successfully: <a href='{permalink}' target='_blank'>View</a>"
        else:
            return "✅ Reel uploaded but unable to retrieve permalink."

    except Exception as e:
        return f"❌ Instagram upload error: {str(e)}"

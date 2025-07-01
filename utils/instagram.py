# File: utils/instagram.py

"""
Handles Instagram Reels posting via Meta Graph API.
Supports video URL upload, publishing, and logging.
"""

import os
import json
import time
import requests
from urllib.parse import urlencode
from utils.user_db import get_instagram_credentials, log_post

INSTAGRAM_API_URL = "https://graph.facebook.com/v19.0"

def post_to_instagram(
    video_path: str,
    caption: str,
    username: str,
    video_url: str = "",
    task_id: str = None
) -> str:
    """
    Uploads a Reel to Instagram via Graph API using a pre-hosted video URL.
    Returns result message (HTML safe).
    """
    creds = get_instagram_credentials(username)
    if not creds:
        return "❌ No Instagram credentials found for user."

    access_token = creds.get("access_token")
    user_id = creds.get("user_id")
    if not access_token or not user_id:
        return "❌ Access token or user ID missing."

    if not video_url:
        return (
            "❌ Missing video_url for Instagram upload. "
            "Direct file uploads not supported via Instagram Graph API unless hosted on a Facebook page."
        )

    try:
        # Step 1: Create media container
        container_url = f"{INSTAGRAM_API_URL}/{user_id}/media"
        payload = {
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "access_token": access_token,
            "share_to_feed": "true"
        }

        r1 = requests.post(container_url, data=payload, timeout=30)
        r1.raise_for_status()
        container_id = r1.json().get("id")

        if not container_id:
            return "❌ Failed to create Instagram media container."

        # Step 2: Publish the media
        publish_url = f"{INSTAGRAM_API_URL}/{user_id}/media_publish"
        r2 = requests.post(publish_url, data={
            "creation_id": container_id,
            "access_token": access_token
        }, timeout=30)
        r2.raise_for_status()
        media_id = r2.json().get("id")

        permalink = "URL not available"
        if media_id:
            # Step 3: Optional - Fetch permalink
            time.sleep(3)  # Let it propagate
            r3 = requests.get(
                f"{INSTAGRAM_API_URL}/{media_id}",
                params={"fields": "permalink", "access_token": access_token},
                timeout=10
            )
            if r3.ok:
                permalink = r3.json().get("permalink", permalink)

        # ✅ Log the post
        log_post(username, video_path=video_path, caption=caption, drive_url=permalink)

        if "http" in permalink:
            return f"📤 Reel posted successfully: <a href='{permalink}' target='_blank'>View</a>"
        else:
            return "✅ Reel uploaded, but permalink unavailable."

    except requests.exceptions.RequestException as e:
        return f"❌ Instagram upload request failed: {str(e)}"
    except Exception as e:
        return f"❌ Instagram upload error: {str(e)}"

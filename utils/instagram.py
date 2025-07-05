# File: utils/instagram.py

"""
Handles Instagram Reels posting via Meta Graph API.
Supports video URL upload, publishing, and logging.
"""

import os
import time
import requests
from urllib.parse import urlencode
from utils.user_db import get_instagram_credentials, log_post

# Constants
INSTAGRAM_API_URL = "https://graph.facebook.com/v19.0"

# Optional UI hook
try:
    from progress import update_progress
except ImportError:
    def update_progress(task_id, status, percent): pass


def post_to_instagram(
    video_path: str,
    caption: str,
    user_name: str,
    video_url: str = "",
    task_id: str = None
) -> str:
    """
    Uploads a Reel to Instagram using a hosted video URL.
    Returns an HTML-safe result message.
    """
    update_progress(task_id, "📡 Connecting to Instagram...", 91)

    creds = get_instagram_credentials(user_name)
    if not creds:
        return "❌ No Instagram credentials found for user."

    access_token = creds.get("access_token")
    user_id = creds.get("user_id")

    if not access_token or not user_id:
        return "❌ Instagram access token or user ID is missing."

    if not video_url or not video_url.startswith("http"):
        return (
            "❌ A valid `video_url` is required for Instagram upload. "
            "Direct uploads are not supported unless using a Facebook Page."
        )

    try:
        # Step 1: Create media container
        update_progress(task_id, "📦 Creating media container...", 93)
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
            return "❌ Failed to create Instagram media container (no ID returned)."

        # Step 2: Publish the media
        update_progress(task_id, "🚀 Publishing to Instagram...", 95)
        publish_url = f"{INSTAGRAM_API_URL}/{user_id}/media_publish"
        r2 = requests.post(publish_url, data={
            "creation_id": container_id,
            "access_token": access_token
        }, timeout=30)
        r2.raise_for_status()
        media_id = r2.json().get("id")

        # Step 3: Optional - Fetch permalink
        permalink = "URL not available"
        if media_id:
            time.sleep(3)  # Allow Instagram time to generate permalink
            r3 = requests.get(
                f"{INSTAGRAM_API_URL}/{media_id}",
                params={"fields": "permalink", "access_token": access_token},
                timeout=10
            )
            if r3.ok:
                permalink = r3.json().get("permalink", permalink)

        # Log it
        log_post(user_name, video_path=video_path, caption=caption, drive_url=permalink)
        update_progress(task_id, "✅ Instagram upload complete", 98)

        if permalink.startswith("http"):
            return f"📤 Reel posted successfully: <a href='{permalink}' target='_blank'>View</a>"
        return "✅ Reel uploaded, but permalink is unavailable."

    except requests.exceptions.RequestException as e:
        return f"❌ Instagram API request failed: {e}"
    except Exception as e:
        return f"❌ Unexpected Instagram upload error: {e}"

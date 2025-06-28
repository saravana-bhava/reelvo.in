# utils/instagram.py

import time
import requests
from utils.google_drive import upload_to_google_drive

# Optional progress support
try:
    from progress import update_progress
except ImportError:
    def update_progress(task_id, status, percent): pass

def post_to_instagram(video_path, caption, ig_account_id, access_token, username="default", video_url=None, task_id=None):
    try:
        update_progress(task_id, "📤 Preparing Instagram upload...", 91)

        # Upload to Drive if URL not provided
        if not video_url:
            update_progress(task_id, "📁 Uploading to Google Drive...", 92)
            video_url, upload_error = upload_to_google_drive(video_path, username, task_id)
            if not video_url or not video_url.startswith("http"):
                return f"[❌] Failed to upload video to Google Drive: {upload_error}"

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
            return f"[❌] Container upload failed: {container_res.text}"

        container_id = container_res.json().get("id")
        update_progress(task_id, "⏳ Waiting for processing...", 95)

        # Wait until Instagram processes the reel
        for i in range(10):
            time.sleep(5)
            status_res = requests.get(
                f"https://graph.facebook.com/v19.0/{container_id}",
                params={
                    "fields": "status_code",
                    "access_token": access_token
                }
            )

            if status_res.status_code == 200 and status_res.json().get("status_code") == "FINISHED":
                update_progress(task_id, "✅ Media ready. Publishing...", 96)
                break
        else:
            return "[❌] Media not ready after waiting."

        publish_res = requests.post(
            f"https://graph.facebook.com/v19.0/{ig_account_id}/media_publish",
            params={
                "creation_id": container_id,
                "access_token": access_token
            }
        )

        if publish_res.status_code != 200:
            return f"[❌] Publishing failed: {publish_res.text}"

        post_id = publish_res.json().get("id")

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
            update_progress(task_id, "🎉 Reel published!", 100)
            return f"[✅] Reel posted: <a href='{permalink}' target='_blank'>{permalink}</a>"

        return f"[✅] Posted (ID: {post_id}), but permalink fetch failed."

    except Exception as e:
        return f"[❌] Unexpected error: {e}"

# ================================================
# File:         utils/instagram.py
# Description:  Post videos to Instagram and fetch profile info
# Framework:    Flask + TailwindCSS
# Version:      1.0.0
# Last Updated: 20 August 2025
# Author:       Saravana Bhava
# Author URL:   https://SazM.in
# ================================================

"""
Handles Instagram Reels posting via Meta Graph API.
Supports video URL upload, publishing, and logging.
"""

import os
import time
import requests
from utils.instagram_db import get_instagram_credentials, log_post_to_db, log_story_to_db
from utils.google_drive import upload_to_google_drive

# Constants
INSTAGRAM_API_URL = "https://graph.facebook.com/v19.0"


def post_to_instagram(
    reel_id: str,
    video_path: str,
    caption: str,
    user_email: str,
    video_url: str = "",
    use_drive: bool = True
) -> str:
    """
    Uploads a Reel to Instagram using a hosted video URL.
    If video_url is not provided, uploads to Google Drive (optional).
    Returns an HTML-safe result message.
    """
    print(f"[INFO] 🚀 Starting post for Reel ID: {reel_id} | User: {user_email}")
    print(f"[INFO] ✏️ Caption (first 50 chars): {caption[:50]}")
    print(f"[INFO] 📁 Local video path: {video_path}")

    creds = get_instagram_credentials(user_email)
    if not creds:
        return "❌ No Instagram credentials found for user."

    access_token = creds.get("access_token")
    user_id = creds.get("platform_user_id")

    if not access_token or not user_id:
        return "❌ Instagram access token or user ID is missing."

    # Upload to Google Drive if needed
    if use_drive and (not video_url or not video_url.startswith("http")):
        print("[INFO] Uploading video to Google Drive...")
        video_url, error = upload_to_google_drive(video_path, user_email)
        if error:
            print(f"[ERROR] Google Drive upload failed: {error}")
            return f"❌ {error}"
    elif not video_url or not video_url.startswith("http"):
        # Generate a direct site-hosted URL if not using Google Drive
        protocol = os.getenv("PROTOCOL", "https")
        host = os.getenv("HOST", "reelvo.in")
        site_base_url = f"{protocol}://{host}"
        filename = os.path.basename(video_path)
        video_url = f"{site_base_url}/videos/{user_email}/{filename}"

    print(f"[INFO] 🔗 Video URL used: {video_url}")

    try:
        # Step 1: Create media container
        print(f"[INFO] 🧪 Creating Instagram media container...")
        container_url = f"{INSTAGRAM_API_URL}/{user_id}/media"
        payload = {
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption[:2200],
            "access_token": access_token,
            "share_to_feed": "true"
        }

        r1 = requests.post(container_url, data=payload, timeout=30)
        r1.raise_for_status()
        container_response = r1.json()
        print(f"[DEBUG] 🧾 Container creation response: {container_response}")

        container_id = container_response.get("id")
        if not container_id:
            print(f"[ERROR] ❌ Container creation failed. Response: {r1.text}")
            return "❌ Failed to create Instagram media container (no ID returned)."

        # Step 1.5: Wait for media container to finish processing
        print(f"[INFO] ⏳ Waiting for container {container_id} to finish processing...")
        for attempt in range(30):  # up to ~90 seconds
            status_check_url = f"{INSTAGRAM_API_URL}/{container_id}"
            status_resp = requests.get(
                status_check_url,
                params={"fields": "status_code", "access_token": access_token},
                timeout=10
            )

            if status_resp.ok:
                status_data = status_resp.json()
                status = status_data.get("status_code")
                print(f"[Attempt {attempt+1}] Container {container_id} status: {status} | Response: {status_data}")

                if status == "FINISHED":
                    print(f"[SUCCESS] ✅ Container {container_id} is ready.")
                    break
                elif status == "ERROR":
                    print(f"[ERROR] ❌ Media processing failed for container ID {container_id} | Response: {status_data}")
                    return f"❌ Media processing failed for container ID {container_id}"
            else:
                print(f"[Attempt {attempt+1}] ⚠️ Failed to fetch status for container {container_id}: {status_resp.text}")

            time.sleep(3)
        else:
            print(f"[ERROR] 🕒 Timeout waiting for container {container_id} to finish.")
            return f"❌ Timeout waiting for container {container_id} to finish processing."

        # Step 2: Publish the media
        print(f"[INFO] 📤 Publishing container {container_id}...")
        publish_url = f"{INSTAGRAM_API_URL}/{user_id}/media_publish"
        r2 = requests.post(publish_url, data={
            "creation_id": container_id,
            "access_token": access_token
        }, timeout=30)
        r2.raise_for_status()
        media_id = r2.json().get("id")
        print(f"[SUCCESS] 📸 Media published. Media ID: {media_id}")

        # Step 3: Optional - Fetch permalink
        permalink = "URL not available"
        if media_id:
            time.sleep(3)
            r3 = requests.get(
                f"{INSTAGRAM_API_URL}/{media_id}",
                params={"fields": "permalink", "access_token": access_token},
                timeout=10
            )
            if r3.ok:
                permalink = r3.json().get("permalink", permalink)
                print(f"[INFO] 🔗 Permalink fetched: {permalink}")
            else:
                print(f"[WARN] ⚠️ Failed to fetch permalink: {r3.text}")

        # Log to DB
        print(f"[INFO] 🗃️ Logging post to DB: Reel ID: {reel_id}, Permalink: {permalink}")
        log_post_to_db(
            reel_id=reel_id,
            permalink=permalink
        )

        if permalink.startswith("http"):
            return f"📤 Reel posted successfully: <a href='{permalink}' target='_blank'>View</a>"
        return "✅ Reel uploaded, but permalink is unavailable."

    except requests.exceptions.HTTPError as e:
        print(f"[EXCEPTION] ❗ API request error for reel {reel_id}: {e}")
        try:
            print(f"[RESPONSE BODY] {e.response.json()}")
        except:
            print(f"[RESPONSE TEXT] {e.response.text}")
        return f"❌ Instagram API request failed: {e}"
    except requests.exceptions.RequestException as e:
        print(f"[EXCEPTION] ❗ API request error for reel {reel_id}: {e}")
        return f"❌ Instagram API request failed: {e}"
    except Exception as e:
        print(f"[EXCEPTION] ❗ Unexpected error while posting reel {reel_id}: {e}")
        return f"❌ Unexpected Instagram upload error: {e}"

# ================================================
# Story posting
# Returns a string that includes "Story posted successfully" for compatibility.
# ================================================
def post_story_to_instagram(
    story_id: str,
    media_path: str,
    caption: str,
    media_type: str,          # "image" | "video"
    user_email: str,
    media_url: str = "",
    use_drive: bool = True
) -> str:
    """
    Uploads a story to Instagram using the dedicated STORIES endpoint.
    Supports both image and video. Waits until container is processed before publishing.
    """
    print(f"[INFO] 🚀 Starting post for Story ID: {story_id} | User: {user_email}")
    print(f"[INFO] ✏️ Caption (first 50 chars): {caption[:50]}")
    print(f"[INFO] 📁 Local media path: {media_path}")

    creds = get_instagram_credentials(user_email)
    if not creds:
        return "❌ No Instagram credentials found for user."

    access_token = creds.get("access_token")
    user_id = creds.get("platform_user_id")
    if not access_token or not user_id:
        return "❌ Instagram access token or user ID is missing."

    # Resolve public URL
    if use_drive and (not media_url or not media_url.startswith("http")):
        print("[INFO] Uploading media to Google Drive for a public URL...")
        media_url, error = upload_to_google_drive(media_path, user_email)
        if error:
            return f"❌ {error}"
    elif not media_url or not media_url.startswith("http"):
        protocol = os.getenv("PROTOCOL", "https")
        host = os.getenv("HOST", "reelvo.in")
        filename = os.path.basename(media_path)
        media_url = f"{protocol}://{host}/stories/{user_email}/{filename}"

    print(f"[INFO] 🔗 Media URL used: {media_url}")
    container_url = f"{INSTAGRAM_API_URL}/{user_id}/media"

    try:
        # -----------------------------
        # Step 1: Create STORIES container
        # -----------------------------
        print("[INFO] 🧪 Creating Instagram STORIES container...")
        payload = {
            "media_type": "STORIES",
            "caption": caption[:2200],
            "access_token": access_token
        }

        if media_type == "image":
            payload["image_url"] = media_url
        elif media_type == "video":
            payload["video_url"] = media_url
        else:
            return "❌ Unsupported media_type for story. Must be 'image' or 'video'."

        r1 = requests.post(container_url, data=payload, timeout=30)
        r1.raise_for_status()
        container_id = r1.json().get("id")
        if not container_id:
            return "❌ Failed to create Instagram story container (no ID returned)."
        print(f"[INFO] 🆔 Container created: {container_id}")

        # -----------------------------
        # Step 1.5: Wait until IG finishes processing
        # -----------------------------
        print(f"[INFO] ⏳ Waiting for container {container_id} to finish processing...")
        for attempt in range(30):  # up to ~90s
            status_resp = requests.get(
                f"{INSTAGRAM_API_URL}/{container_id}",
                params={"fields": "status_code", "access_token": access_token},
                timeout=10
            )
            if status_resp.ok:
                status_data = status_resp.json()
                status = status_data.get("status_code")
                print(f"[Attempt {attempt+1}] Container {container_id} status: {status} | Response: {status_data}")

                if status == "FINISHED":
                    print(f"[SUCCESS] ✅ Container {container_id} is ready.")
                    break
                elif status in ("ERROR", "EXPIRED"):
                    return f"❌ Media processing failed for container ID {container_id}"
            else:
                print(f"[Attempt {attempt+1}] ⚠️ Failed to fetch status: {status_resp.text}")

            time.sleep(3)
        else:
            return f"❌ Timeout waiting for container {container_id} to finish processing."

        # -----------------------------
        # Step 2: Publish STORIES container
        # -----------------------------
        print(f"[INFO] 📤 Publishing STORIES container {container_id}...")
        publish_url = f"{INSTAGRAM_API_URL}/{user_id}/media_publish"
        r2 = requests.post(publish_url, data={
            "creation_id": container_id,
            "access_token": access_token
        }, timeout=30)
        r2.raise_for_status()
        media_id = r2.json().get("id")
        print(f"[SUCCESS] 🎉 Story published. Media ID: {media_id}")

        # No permalink for stories (they expire)
        log_story_to_db(story_id=story_id, permalink="(story, no permalink)")

        return "📤 Story posted successfully 🎉"

    except requests.exceptions.HTTPError as e:
        try:
            body = e.response.json()
        except Exception:
            body = e.response.text
        print(f"[EXCEPTION] ❗ API request error for story {story_id}: {e} | {body}")
        return f"❌ Instagram API request failed: {e}"
    except Exception as e:
        print(f"[EXCEPTION] ❗ Unexpected error while posting story {story_id}: {e}")
        return f"❌ Unexpected Instagram upload error: {e}"


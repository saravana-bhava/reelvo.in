import time
import requests
from utils.google_drive import upload_to_google_drive

def upload_to_temp_hosting(local_path, username="default"):
    return upload_to_google_drive(local_path, username)  # returns (url, error)

def post_to_instagram(video_path, caption, ig_account_id, access_token, username="default"):
    public_video_url, error = upload_to_temp_hosting(video_path, username)

    if error or not public_video_url or not public_video_url.startswith("http"):
        return f"[❌] Failed to upload video to Google Drive: {error or 'Unknown error'}"

    print(f"[📤] Uploading reel to Instagram container...")
    res = requests.post(f"https://graph.facebook.com/v19.0/{ig_account_id}/media", params={
        "media_type": "REELS",
        "video_url": public_video_url,
        "caption": caption,
        "access_token": access_token,
        "share_to_feed": "true"
    })

    if res.status_code != 200:
        return f"[❌] Container upload failed: {res.text}"

    container_id = res.json().get("id")
    time.sleep(5)

    res = requests.post(f"https://graph.facebook.com/v19.0/{ig_account_id}/media_publish", params={
        "creation_id": container_id,
        "access_token": access_token
    })

    if res.status_code != 200:
        return f"[❌] Publishing failed: {res.text}"

    return res.json().get("id")

import time
import requests
from utils.google_drive import upload_to_google_drive

def upload_to_temp_hosting(local_path, username="default"):
    return upload_to_google_drive(local_path, username)

def post_to_instagram(video_path, caption, ig_account_id, access_token, username="default"):
    public_video_url, upload_error = upload_to_temp_hosting(video_path, username)

    if not public_video_url or not public_video_url.startswith("http"):
        return f"[❌] Failed to upload video to Google Drive: {upload_error}"

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

    print("[⏳] Waiting for media processing...")
    for _ in range(10):
        time.sleep(5)
        check = requests.get(f"https://graph.facebook.com/v19.0/{container_id}", params={
            "fields": "status_code",
            "access_token": access_token
        })

        if check.status_code == 200 and check.json().get("status_code") == "FINISHED":
            print("[✅] Media is ready. Publishing...")
            break
    else:
        return "[❌] Media is not ready for publishing."

    publish = requests.post(f"https://graph.facebook.com/v19.0/{ig_account_id}/media_publish", params={
        "creation_id": container_id,
        "access_token": access_token
    })

    if publish.status_code != 200:
        return f"[❌] Publishing failed: {publish.text}"

    post_id = publish.json().get("id")

    # ✅ Get permalink URL
    permalink_res = requests.get(f"https://graph.facebook.com/v19.0/{post_id}", params={
        "fields": "permalink",
        "access_token": access_token
    })

    if permalink_res.status_code == 200:
        permalink = permalink_res.json().get("permalink")
        return f"[✅] Reel posted successfully: <a href='{permalink}' target='_blank'>{permalink}</a>"
    else:
        return f"[✅] Posted (ID: {post_id}), but failed to fetch permalink."


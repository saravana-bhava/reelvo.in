import os
import time
from flask import Flask, render_template, request, redirect, session, url_for, send_from_directory
from dotenv import load_dotenv
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple

from utils.generate_script import generate_script_for_user
from create_video import create_video_for_category
from utils.instagram import post_to_instagram
from utils.google_drive import upload_to_google_drive  # ✅ Unified Google Drive uploader

load_dotenv()

flask_app = Flask(__name__)
flask_app.secret_key = os.getenv("FLASK_SECRET_KEY", "demo_secret")
OUTPUT_BASE = "output"

# Instagram config
POST_TO_IG = os.getenv("POST_TO_IG", "false").lower() == "true"
IG_ACCOUNT_ID = os.getenv("INSTAGRAM_BUSINESS_ID")
IG_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN")

@flask_app.route('/')
def index():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return render_template("login.html")

@flask_app.route('/login', methods=["POST"])
def login():
    session["user"] = request.form["username"].strip()
    return redirect(url_for("dashboard"))

@flask_app.route('/logout')
def logout():
    session.pop("user", None)
    return redirect(url_for("index"))

@flask_app.route('/dashboard')
def dashboard():
    if "user" not in session:
        return redirect(url_for("index"))

    username = session["user"]
    user_output_dir = os.path.join(OUTPUT_BASE, username)
    videos = [f for f in os.listdir(user_output_dir) if f.endswith(".mp4")] if os.path.exists(user_output_dir) else []

    return render_template("dashboard.html", user=username, videos=videos)

@flask_app.route('/generate', methods=["POST"])
def generate():
    if "user" not in session:
        return redirect(url_for("index"))

    username = session["user"]
    theme = request.form.get("theme", "default").lower()

    try:
        script_path = generate_script_for_user(theme, username)
        with open(script_path, "r", encoding="utf-8") as f:
            script = f.read().strip()

        video_path = create_video_for_category(theme, username)
        status = f"✅ Reel generated for <b>{theme}</b>" if video_path else f"❌ Video generation failed for {theme}"

        if video_path:
            # ✅ Upload to Google Drive
            drive_url, drive_error = upload_to_google_drive(video_path, username)
            if drive_url and drive_url.startswith("http"):
                status += f"<br>📁 Uploaded to Drive: <a href='{drive_url}' target='_blank'>Open</a>"
            else:
                status += f"<br>{drive_error or '[❌] Unknown upload error.'}"

        # ✅ Optional: Auto-post to IG
        if POST_TO_IG and video_path and IG_ACCOUNT_ID and IG_ACCESS_TOKEN:
            print("[📲] Auto-posting to Instagram...")
            caption = f"{theme.capitalize()} Reel by {username}"
            post_result = post_to_instagram(video_path, caption, IG_ACCOUNT_ID, IG_ACCESS_TOKEN, username)
            print(f"[📲] Post Result: {post_result}")
            status += f"<br>{post_result}"

    except Exception as e:
        script = ""
        status = f"❌ Error: {str(e)}"

    user_output_dir = os.path.join(OUTPUT_BASE, username)
    videos = [f for f in os.listdir(user_output_dir) if f.endswith(".mp4")] if os.path.exists(user_output_dir) else []

    return render_template("dashboard.html", user=username, script=script, status=status, videos=videos)

@flask_app.route('/videos/<username>/<filename>')
def serve_video(username, filename):
    return send_from_directory(os.path.join(OUTPUT_BASE, username), filename)

# Mount app under subpath `/reelvo.ai`
application = DispatcherMiddleware(lambda e, s: s(b'404 Not Found', []), {
    '/reelvo.ai': flask_app
})

# For production deployment via Gunicorn, Railway, Render, etc.
app = application

# For local development
if __name__ == "__main__":
    os.makedirs(OUTPUT_BASE, exist_ok=True)
    port = int(os.environ.get("PORT", 5000))
    run_simple("127.0.0.1", port, app, use_debugger=True, use_reloader=True)

# app.py

import os
import time
import logging
from flask import Flask, render_template, request, redirect, session, url_for, send_from_directory, abort
from dotenv import load_dotenv
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple
from werkzeug.utils import secure_filename

from utils.generate_script import generate_script_for_user
from create_video import create_video_for_category
from utils.instagram import post_to_instagram
from utils.google_drive import upload_to_google_drive

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("reelvo")

# Flask app
flask_app = Flask(__name__)
flask_app.secret_key = os.getenv("FLASK_SECRET_KEY", "demo_secret")

# Constants
OUTPUT_BASE = "output"
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
    username = request.form["username"].strip()
    if not username:
        return redirect(url_for("index"))
    session["user"] = secure_filename(username)
    return redirect(url_for("dashboard"))


@flask_app.route('/logout')
def logout():
    session.pop("user", None)
    return redirect(url_for("index"))


@flask_app.route('/dashboard')
def dashboard():
    if "user" not in session:
        return redirect(url_for("index"))

    username = secure_filename(session["user"])
    user_output_dir = os.path.join(OUTPUT_BASE, username)
    videos = [f for f in os.listdir(user_output_dir) if f.endswith(".mp4")] if os.path.exists(user_output_dir) else []

    return render_template("dashboard.html", user=username, videos=videos)


@flask_app.route('/generate', methods=["POST"])
def generate():
    if "user" not in session:
        return redirect(url_for("index"))

    username = secure_filename(session["user"])
    theme = request.form.get("theme", "default").lower()

    script = ""
    status = ""

    try:
        script_path = generate_script_for_user(theme, username)
        with open(script_path, "r", encoding="utf-8") as f:
            script = f.read().strip()

        video_path = create_video_for_category(theme, username)
        if video_path:
            status = f"✅ Reel generated for <b>{theme}</b>"
        else:
            status = f"❌ Video generation failed for {theme}"

        # Upload to Google Drive
        drive_url, drive_error = None, None
        if video_path:
            drive_url, drive_error = upload_to_google_drive(video_path, username)
            if drive_url and drive_url.startswith("http"):
                status += f"<br>📁 Uploaded to Drive: <a href='{drive_url}' target='_blank'>Open</a>"
            else:
                status += f"<br>{drive_error or '[❌] Unknown upload error.'}"

        # Auto-post to Instagram
        if POST_TO_IG and video_path and IG_ACCOUNT_ID and IG_ACCESS_TOKEN:
            logger.info("[📲] Auto-posting to Instagram...")
            caption = f"{theme.capitalize()} Reel by {username}"
            post_result = post_to_instagram(
                video_path,
                caption,
                IG_ACCOUNT_ID,
                IG_ACCESS_TOKEN,
                username,
                video_url=drive_url
            )
            logger.info(f"[📲] Post Result: {post_result}")
            status += f"<br>{post_result}"

    except Exception as e:
        logger.exception("Error during generation")
        status = f"❌ Error: {str(e)}"

    # Refresh video list
    user_output_dir = os.path.join(OUTPUT_BASE, username)
    videos = [f for f in os.listdir(user_output_dir) if f.endswith(".mp4")] if os.path.exists(user_output_dir) else []

    return render_template("dashboard.html", user=username, script=script, status=status, videos=videos)


@flask_app.route('/videos/<username>/<filename>')
def serve_video(username, filename):
    safe_user = secure_filename(username)
    safe_file = secure_filename(filename)
    path = os.path.join(OUTPUT_BASE, safe_user)
    full_path = os.path.join(path, safe_file)

    if not os.path.exists(full_path):
        abort(404)

    return send_from_directory(path, safe_file)


# Mount app under subpath `/reelvo.ai`
application = DispatcherMiddleware(lambda e, s: s(b'404 Not Found', []), {
    '/reelvo.ai': flask_app
})

# WSGI entrypoint (e.g., Gunicorn)
app = application

# Local dev
if __name__ == "__main__":
    os.makedirs(OUTPUT_BASE, exist_ok=True)
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"Starting development server on http://127.0.0.1:{port}")
    run_simple("127.0.0.1", port, app, use_debugger=True, use_reloader=True)

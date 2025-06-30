# File: app.py

import os
import time
import logging
import uuid
import json
import requests
from threading import Thread
from flask import (
    Flask, render_template, request, redirect, session,
    url_for, send_from_directory, abort, jsonify
)
from dotenv import load_dotenv
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple
from werkzeug.utils import secure_filename

from utils.generate_script import generate_script_for_user
from create_video import create_video_for_category
from utils.instagram import post_to_instagram
from utils.google_drive import upload_to_google_drive
from progress import (
    progress_status, start_progress,
    update_progress, finish_progress, get_progress
)

# Load environment variables
load_dotenv()

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("reelvo")

# Flask setup
flask_app = Flask(__name__)
flask_app.secret_key = os.getenv("FLASK_SECRET_KEY", "demo_secret")
if flask_app.secret_key == "demo_secret":
    logger.warning("⚠️ Using default Flask secret key — not safe for production.")

# Constants
OUTPUT_BASE = "output"
POST_TO_IG = os.getenv("POST_TO_IG", "false").lower() == "true"
UPLOAD_TO_DRIVE = os.getenv("UPLOAD_TO_DRIVE", "false").lower() == "true"
IG_ACCOUNT_ID = os.getenv("INSTAGRAM_BUSINESS_ID")
IG_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN")
FB_APP_ID = os.getenv("FB_APP_ID")
FB_APP_SECRET = os.getenv("FB_APP_SECRET")
FB_REDIRECT_URI = os.getenv("FB_REDIRECT_URI")


# ----------------- Routes -----------------

@flask_app.route('/')
def index():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return render_template("login.html")


@flask_app.route('/login', methods=["POST"])
def login():
    username = request.form.get("username", "").strip()
    if not username:
        return redirect(url_for("index"))
    session["user"] = secure_filename(username)
    return redirect(url_for("dashboard"))


@flask_app.route('/logout')
def logout():
    session.pop("user", None)
    return redirect(url_for("index"))


@flask_app.route('/dashboard', methods=["GET"])
def dashboard():
    if "user" not in session:
        return redirect(url_for("index"))
    username = secure_filename(session["user"])
    return render_template("dashboard.html", user=username)


@flask_app.route('/connect-instagram')
def connect_instagram():
    if "user" not in session:
        return redirect(url_for("index"))

    oauth_url = (
        f"https://www.facebook.com/v18.0/dialog/oauth?"
        f"client_id={FB_APP_ID}&redirect_uri={FB_REDIRECT_URI}"
        f"&scope=pages_show_list,instagram_basic,pages_read_engagement,"
        f"pages_manage_posts,instagram_content_publish"
    )
    return redirect(oauth_url)


@flask_app.route('/instagram/callback')
def instagram_callback():
    if "user" not in session:
        return redirect(url_for("index"))

    code = request.args.get("code")
    username = secure_filename(session["user"])
    if not code:
        return "❌ Missing OAuth code", 400

    try:
        token_url = "https://graph.facebook.com/v18.0/oauth/access_token"
        token_res = requests.get(token_url, params={
            "client_id": FB_APP_ID,
            "client_secret": FB_APP_SECRET,
            "redirect_uri": FB_REDIRECT_URI,
            "code": code
        }).json()
        access_token = token_res.get("access_token")
        if not access_token:
            return f"❌ Failed to get access_token: {token_res}", 400

        # Get page
        pages_res = requests.get("https://graph.facebook.com/v18.0/me/accounts", params={
            "access_token": access_token
        }).json()
        pages = pages_res.get("data", [])
        if not pages:
            return "❌ No connected Facebook Pages found.", 400

        page = pages[0]
        page_token = page["access_token"]
        page_id = page["id"]

        # Get IG Business ID
        ig_res = requests.get(f"https://graph.facebook.com/v18.0/{page_id}", params={
            "fields": "instagram_business_account",
            "access_token": page_token
        }).json()
        ig_account_id = ig_res.get("instagram_business_account", {}).get("id")
        if not ig_account_id:
            return "❌ Instagram Business account not linked.", 400

        # Save tokens to file
        os.makedirs(os.path.join(OUTPUT_BASE, username), exist_ok=True)
        with open(os.path.join(OUTPUT_BASE, username, "tokens.json"), "w") as f:
            json.dump({
                "access_token": page_token,
                "page_id": page_id,
                "ig_account_id": ig_account_id
            }, f, indent=2)

        return redirect(url_for("dashboard"))
    except Exception as e:
        logger.exception("Instagram OAuth failed")
        return f"❌ Error: {str(e)}", 500


@flask_app.route('/create', methods=["GET"])
def create_reel():
    if "user" not in session:
        return redirect(url_for("index"))

    username = secure_filename(session["user"])
    user_output_dir = os.path.join(OUTPUT_BASE, username)
    videos = [f for f in os.listdir(user_output_dir) if f.endswith(".mp4")] if os.path.exists(user_output_dir) else []

    last_script_path = os.path.join(user_output_dir, "last_script.txt")
    script = None
    if os.path.exists(last_script_path):
        with open(last_script_path, "r", encoding="utf-8") as f:
            script = f.read()

    return render_template("create_reel.html", user=username, videos=videos, script=script)


@flask_app.route('/create_reel', methods=["POST"])
def create_reel_action():
    if "user" not in session:
        return redirect(url_for("index"))

    username = secure_filename(session["user"])
    script = request.form.get("script", "").strip()
    language = request.form.get("language", "en").strip()
    voice_option = request.form.get("voice_option", "tts")
    voice_artist = request.form.get("voice_artist", "en_male_energetic")
    subtitles = 'subtitles' in request.form
    watermark = 'watermark' in request.form
    voice_file = request.files.get("custom_voice")

    task_id = str(uuid.uuid4())
    start_progress(task_id)

    def thread_job():
        try:
            update_progress(task_id, "🎬 Generating reel...", 20)

            video_path = create_video_for_category(
                theme="custom",
                username=username,
                script_text=script,
                voiceover_path=voice_file if voice_option == "upload" and voice_file else None,
                tts_voice=voice_artist,
                language=language,
                include_subtitles=subtitles,
                include_watermark=watermark,
                task_id=task_id
            )

            drive_url = ""
            if video_path:
                if UPLOAD_TO_DRIVE:
                    update_progress(task_id, "📤 Uploading to Drive...", 80)
                    drive_url, err = upload_to_google_drive(video_path, username, task_id)
                    if drive_url:
                        finish_progress(task_id, f"✅ Done. <a href='{drive_url}' target='_blank'>View Reel</a>")
                    else:
                        finish_progress(task_id, f"✅ Reel created. Drive upload failed: {err}", 100)
                else:
                    finish_progress(task_id, "✅ Reel created (not uploaded)", 100)

                token_file = os.path.join(OUTPUT_BASE, username, "tokens.json")
                if POST_TO_IG and os.path.exists(token_file):
                    with open(token_file, "r") as f:
                        creds = json.load(f)
                    post_result = post_to_instagram(
                        video_path=video_path,
                        caption=f"Custom Reel by {username}",
                        ig_account_id=creds["ig_account_id"],
                        access_token=creds["access_token"],
                        username=username,
                        video_url=drive_url,
                        task_id=task_id
                    )
                    progress_status[task_id]["status"] += f"<br>{post_result}"
            else:
                finish_progress(task_id, "❌ Video generation failed", -1)

        except Exception as e:
            logger.exception("❌ Error generating reel")
            finish_progress(task_id, f"❌ Error: {str(e)}", -1)

    Thread(target=thread_job).start()
    return redirect(url_for("dashboard"))


@flask_app.route('/history', methods=["GET"])
def list_reels():
    if "user" not in session:
        return redirect(url_for("index"))

    username = secure_filename(session["user"])
    user_output_dir = os.path.join(OUTPUT_BASE, username)
    videos = [f for f in os.listdir(user_output_dir) if f.endswith(".mp4")] if os.path.exists(user_output_dir) else []

    scripts = {}
    for video in videos:
        base = os.path.splitext(video)[0]
        script_path = os.path.join(user_output_dir, f"{base}.txt")
        if os.path.exists(script_path):
            with open(script_path, "r", encoding="utf-8") as f:
                scripts[video] = f.read()
        else:
            scripts[video] = "No script found."

    return render_template("list_reels.html", user=username, videos=videos, scripts=scripts)


@flask_app.route('/generate-script', methods=["POST"])
def generate_script_ajax():
    if "user" not in session:
        return jsonify({"error": "Not logged in"}), 401

    data = request.get_json()
    theme = data.get("theme", "").strip()
    custom_topic = data.get("custom_topic", "").strip()
    language = data.get("language", "en").strip()
    username = secure_filename(session["user"])

    try:
        if custom_topic:
            script = generate_script_for_user(custom_topic, username, language=language, custom=True)
        elif theme:
            script = generate_script_for_user(theme, username, language=language)
        else:
            return jsonify({"error": "Missing theme or topic"}), 400

        user_output_dir = os.path.join(OUTPUT_BASE, username)
        os.makedirs(user_output_dir, exist_ok=True)
        last_script_path = os.path.join(user_output_dir, "last_script.txt")
        with open(last_script_path, "w", encoding="utf-8") as f:
            f.write(script)

        return jsonify({"script": script})
    except Exception as e:
        logger.exception("Script generation failed")
        return jsonify({"error": str(e)}), 500


@flask_app.route("/progress/<task_id>")
def get_progress_route(task_id):
    prog = get_progress(task_id)
    start_time = progress_status.get(task_id, {}).get("start_time", None)
    prog["elapsed"] = int(time.time() - start_time) if start_time else 0
    return jsonify(prog)


@flask_app.route('/videos/<username>/<filename>')
def serve_video(username, filename):
    safe_user = secure_filename(username)
    safe_file = secure_filename(filename)
    path = os.path.join(OUTPUT_BASE, safe_user)
    full_path = os.path.join(path, safe_file)

    if not os.path.exists(full_path):
        abort(404)

    return send_from_directory(path, safe_file, mimetype="video/mp4")


# ----------------- WSGI Application -----------------

wsgi_app = DispatcherMiddleware(
    lambda environ, start_response: start_response("404 Not Found", []) or [b"404 Not Found"],
    {"/reelvo.ai": flask_app}
)


# ----------------- Local Dev Server -----------------

if __name__ == "__main__":
    os.makedirs(OUTPUT_BASE, exist_ok=True)
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"🚀 Starting dev server on http://127.0.0.1:{port}/reelvo.ai")
    run_simple("127.0.0.1", port, wsgi_app, use_debugger=True, use_reloader=True)

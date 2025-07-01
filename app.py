# File: app.py

import os
import time
import json
import logging
import uuid
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

# ----------------- Load Environment -----------------

load_dotenv()

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("reelvo")

# Flask app
flask_app = Flask(__name__)
flask_app.secret_key = os.getenv("FLASK_SECRET_KEY", "demo_secret")

# Constants
OUTPUT_BASE = "output"
POST_TO_IG = os.getenv("POST_TO_IG", "false").lower() == "true"
UPLOAD_TO_DRIVE = os.getenv("UPLOAD_TO_DRIVE", "false").lower() == "true"
IG_APP_ID = os.getenv("IG_APP_ID")
IG_APP_SECRET = os.getenv("IG_APP_SECRET")
IG_REDIRECT_URI = os.getenv("IG_REDIRECT_URI", "http://localhost:5000/reelvo.ai/connect-instagram/callback")

# ----------------- Token Refresher -----------------

def refresh_instagram_tokens():
    logger.info("🔄 Starting Instagram token refresher thread...")
    while True:
        for username in os.listdir(OUTPUT_BASE):
            user_dir = os.path.join(OUTPUT_BASE, username)
            tokens_path = os.path.join(user_dir, "tokens.json")
            if not os.path.exists(tokens_path):
                continue
            try:
                with open(tokens_path, "r") as f:
                    tokens = json.load(f)
                if "long_lived_token" not in tokens:
                    continue
                refresh_url = (
                    f"https://graph.instagram.com/refresh_access_token"
                    f"?grant_type=ig_refresh_token&access_token={tokens['long_lived_token']}"
                )
                r = requests.get(refresh_url)
                if r.ok:
                    data = r.json()
                    tokens["long_lived_token"] = data.get("access_token", tokens["long_lived_token"])
                    tokens["expires_in"] = data.get("expires_in", None)
                    with open(tokens_path, "w") as f:
                        json.dump(tokens, f, indent=2)
                    logger.info(f"[✅] Refreshed token for {username}")
            except Exception as e:
                logger.warning(f"[❌] Token refresh error for {username}: {e}")
        time.sleep(24 * 3600)

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


@flask_app.route('/dashboard')
def dashboard():
    if "user" not in session:
        return redirect(url_for("index"))
    username = secure_filename(session["user"])
    user_dir = os.path.join(OUTPUT_BASE, username)
    connected = False
    tokens_path = os.path.join(user_dir, "tokens.json")
    if os.path.exists(tokens_path):
        try:
            with open(tokens_path) as f:
                data = json.load(f)
            if "long_lived_token" in data:
                connected = True
        except:
            pass
    return render_template("dashboard.html", user=username, connected=connected)


@flask_app.route('/connect-instagram')
def connect_instagram():
    if "user" not in session:
        return redirect(url_for("index"))

    client_id = os.getenv("IG_CLIENT_ID")
    redirect_uri = os.getenv("IG_REDIRECT_URI")
    scopes = "user_profile,user_media"
    auth_url = f"https://api.instagram.com/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&scope={scopes}&response_type=code"
    return redirect(auth_url)


#@flask_app.route('/connect-instagram')
#def connect_instagram():
#    if "user" not in session:
#        return redirect(url_for("index"))
#    state = session["user"]
#    auth_url = (
#        f"https://api.instagram.com/oauth/authorize"
#        f"?client_id={IG_APP_ID}&redirect_uri={IG_REDIRECT_URI}"
#        f"&scope=user_profile,user_media&response_type=code&state={state}"
#    )
#    return redirect(auth_url)


@flask_app.route('/connect-instagram/callback')
def connect_instagram_callback():
    code = request.args.get("code")
    state = request.args.get("state")
    if not code or not state:
        return "❌ Missing code/state from Instagram", 400
    username = secure_filename(state)
    user_dir = os.path.join(OUTPUT_BASE, username)
    os.makedirs(user_dir, exist_ok=True)

    try:
        r = requests.post("https://api.instagram.com/oauth/access_token", data={
            "client_id": IG_APP_ID,
            "client_secret": IG_APP_SECRET,
            "grant_type": "authorization_code",
            "redirect_uri": IG_REDIRECT_URI,
            "code": code
        })
        r.raise_for_status()
        data = r.json()
        short_token = data.get("access_token")
        user_id = data.get("user_id")

        r2 = requests.get("https://graph.instagram.com/access_token", params={
            "grant_type": "ig_exchange_token",
            "client_secret": IG_APP_SECRET,
            "access_token": short_token
        })
        r2.raise_for_status()
        long_token_data = r2.json()

        with open(os.path.join(user_dir, "tokens.json"), "w") as f:
            json.dump({
                "user_id": user_id,
                "short_lived_token": short_token,
                "long_lived_token": long_token_data.get("access_token"),
                "expires_in": long_token_data.get("expires_in"),
            }, f, indent=2)

        return redirect(url_for("dashboard"))

    except Exception as e:
        logger.exception("Instagram connect error")
        return f"❌ Instagram connect failed: {e}", 500


@flask_app.route('/auth-callback')
def auth_callback():
    code = request.args.get("code")
    if not code or "user" not in session:
        return "Missing code or session", 400

    username = secure_filename(session["user"])
    try:
        res = requests.post("https://api.instagram.com/oauth/access_token", data={
            "client_id": os.getenv("IG_CLIENT_ID"),
            "client_secret": os.getenv("IG_CLIENT_SECRET"),
            "grant_type": "authorization_code",
            "redirect_uri": os.getenv("IG_REDIRECT_URI"),
            "code": code
        })
        data = res.json()
        save_user_tokens(username, data["access_token"], data.get("refresh_token", ""), data["expires_in"])
        return redirect(url_for("dashboard"))
    except Exception as e:
        logger.exception("Auth failed")
        return f"Auth failed: {str(e)}", 500


@flask_app.route("/token-status")
def token_status():
    if "user" not in session:
        return jsonify({"status": "🔒 Not logged in"}), 401

    tokens = load_user_tokens(session["user"])
    if not tokens:
        return jsonify({"status": "❌ Not connected"})

    expires_at = tokens.get("expires_at", "unknown")
    return jsonify({"status": f"✅ Connected | Expires at: {expires_at}"})


@flask_app.route('/create')
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
                if POST_TO_IG:
                    caption = f"Custom Reel by {username}"
                    post_result = post_to_instagram(
                        video_path=video_path,
                        caption=caption,
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


@flask_app.route('/history')
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


# ----------------- WSGI App -----------------

wsgi_app = DispatcherMiddleware(
    lambda environ, start_response: start_response("404 Not Found", []) or [b"404 Not Found"],
    {"/reelvo.ai": flask_app}
)


# ----------------- Run Dev Server -----------------

if __name__ == "__main__":
    os.makedirs(OUTPUT_BASE, exist_ok=True)
    Thread(target=refresh_instagram_tokens, daemon=True).start()
    port = int(os.getenv("PORT", 5000))
    logger.info(f"🚀 Starting dev server on http://127.0.0.1:{port}/reelvo.ai")
    run_simple("127.0.0.1", port, wsgi_app, use_debugger=True, use_reloader=True)

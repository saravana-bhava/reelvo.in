import os
from flask import Flask, render_template, request, redirect, session, url_for, send_from_directory
from utils.generate_script import generate_script
from create_video import create_video_for_category
from dotenv import load_dotenv
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple

load_dotenv()

# Main Flask app
flask_app = Flask(__name__)
flask_app.secret_key = os.getenv("FLASK_SECRET_KEY", "demo_secret")

OUTPUT_BASE = "output"

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

    username = session.get("user")
    user_output_dir = os.path.join(OUTPUT_BASE, username)
    videos = []

    if os.path.exists(user_output_dir):
        videos = [f for f in os.listdir(user_output_dir) if f.endswith(".mp4")]

    return render_template("dashboard.html", user=username, videos=videos)

@flask_app.route('/generate', methods=["POST"])
def generate():
    if "user" not in session:
        return redirect(url_for("index"))

    username = session.get("user")
    theme = request.form.get("theme", "default").lower()
    script = generate_script(theme)

    user_output_dir = os.path.join(OUTPUT_BASE, username)
    os.makedirs(user_output_dir, exist_ok=True)

    text_file_path = os.path.join(user_output_dir, f"{theme}_text.txt")
    with open(text_file_path, "w") as f:
        f.write(script)

    try:
        video_path = create_video_for_category(theme, username)
        if video_path:
            status = f"✅ Reel generated for <b>{theme}</b>"
        else:
            status = f"❌ Video generation failed for {theme}"
    except Exception as e:
        status = f"❌ Error: {str(e)}"

    videos = [f for f in os.listdir(user_output_dir) if f.endswith(".mp4")]

    return render_template("dashboard.html", user=username, script=script, status=status, videos=videos)

@flask_app.route('/videos/<username>/<filename>')
def serve_video(username, filename):
    return send_from_directory(os.path.join(OUTPUT_BASE, username), filename)

# Mount Flask app under subpath `/reelvo.ai`
application = DispatcherMiddleware(lambda e, s: s(b'404 Not Found', []), {
    '/reelvo.ai': flask_app
})

# Expose as 'app' for Gunicorn / Render / Railway compatibility
app = application

# Run for local development
if __name__ == "__main__":
    if not os.path.exists("output"):
        os.makedirs("output")

    port = int(os.environ.get("PORT", 5000))
    run_simple("127.0.0.1", port, app, use_debugger=True, use_reloader=True)

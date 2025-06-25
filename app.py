import os
from flask import Flask, render_template, request, redirect, session, url_for
#from utils.fallback_ffmpeg import fallback_ffmpeg
from utils.generate_script import generate_script
from dotenv import load_dotenv
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple

load_dotenv()

# Main Flask app
flask_app = Flask(__name__)
flask_app.secret_key = os.getenv("FLASK_SECRET_KEY", "demo_secret")

@flask_app.route('/')
def index():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return render_template("login.html")

@flask_app.route('/login', methods=["POST"])
def login():
    session["user"] = request.form["username"]
    return redirect(url_for("dashboard"))

@flask_app.route('/logout')
def logout():
    session.pop("user", None)
    return redirect(url_for("index"))

@flask_app.route('/dashboard', methods=["GET"])
def dashboard():
    if "user" not in session:
        return redirect(url_for("index"))
    return render_template("dashboard.html", user=session.get("user"))

@flask_app.route('/generate', methods=["POST"])
def generate():
    if "user" not in session:
        return redirect(url_for("index"))

    theme = request.form.get("theme", "default").lower()
    script = generate_script(theme)

    #video_path, method = fallback_ffmpeg(script, theme=theme)
    #if video_path:
        #status = f"Fallback video generated ✅<br>Saved at: {video_path}"
    #else:
        #status = "❌ FFmpeg fallback failed. Please check logs."

    status = "Script Generated"

    return render_template("dashboard.html", user=session.get("user"), script=script, status=status)

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

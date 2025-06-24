# ------------------ app.py ------------------
import os
from flask import Flask, render_template, request, redirect, session
from utils.generate_script import generate_script
from utils.create_video import try_veed_ai, fallback_ffmpeg
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "demo_secret")  # Use env secret or fallback

@app.route('/')
def index():
    # Redirect to dashboard if already logged in
    if "user" in session:
        return redirect("/dashboard")
    return render_template("login.html")

@app.route('/login', methods=["POST"])
def login():
    session["user"] = request.form["username"]
    return redirect("/dashboard")

@app.route('/logout')
def logout():
    session.pop("user", None)
    return redirect("/")

@app.route('/dashboard', methods=["GET"])
def dashboard():
    if "user" not in session:
        return redirect("/")
    return render_template("dashboard.html", user=session.get("user"))

@app.route('/generate', methods=["POST"])
def generate():
    if "user" not in session:
        return redirect("/")

    theme = request.form.get("theme", "default").lower()
    script = generate_script(theme)

    # Try VEED first
    video_url, method = try_veed_ai(script)

    if method == "veed" and video_url:
        status = f"Video generated using VEED.ai ✅<br><a href='{video_url}' target='_blank'>Watch Video</a>"
    else:
        video_path, method = fallback_ffmpeg(script, theme=theme)
        if video_path:
            status = f"VEED failed. Fallback video used ✅<br>Saved at: {video_path}"
        else:
            status = "❌ Both VEED and FFmpeg failed. Please check logs or fallback videos."

    return render_template("dashboard.html", user=session.get("user"), script=script, status=status)

if __name__ == "__main__":
    if not os.path.exists("output"):
        os.makedirs("output")

    port = int(os.environ.get("PORT", 5000))  # For Render or local dev
    app.run(host="0.0.0.0", port=port, debug=True)

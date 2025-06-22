
from flask import Flask, render_template, request, redirect, session
import os
from utils.generate_script import generate_script
from utils.create_video import try_veed_ai, fallback_moviepy

app = Flask(__name__)
app.secret_key = "demo_secret"

@app.route('/')
def index():
    return render_template("login.html")

@app.route('/login', methods=["POST"])
def login():
    session["user"] = request.form["username"]
    return redirect("/dashboard")

@app.route('/dashboard', methods=["GET"])
def dashboard():
    return render_template("dashboard.html", user=session.get("user"))

@app.route('/generate', methods=["POST"])
def generate():
    theme = request.form["theme"]
    script = generate_script(theme)
    
    # Try VEED first
    video_url, method = try_veed_ai(script)
    
    if method == "veed":
        status = f"Video generated using VEED.ai ✅<br><a href='{video_url}' target='_blank'>Watch Video</a>"
    else:
        video_path, method = fallback_moviepy(script)
        status = f"VEED failed. Fallback to local video ✅<br>Saved at: {video_path}"

    return render_template("dashboard.html", user=session.get("user"), script=script, status=status)

if __name__ == "__main__":
    if not os.path.exists("output"):
        os.makedirs("output")
    app.run(debug=True)

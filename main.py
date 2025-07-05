# File: main.py

import os
import logging
from flask import Flask
from threading import Thread
from werkzeug.serving import run_simple
# from waitress import serve  # Uncomment this for real production use

from utils.scheduler import scheduler_runner
from utils.instagram_token_refresher import refresh_instagram_tokens
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.reels import reels_bp
from routes.progress import progress_bp
from routes.instagram import instagram_bp
from routes.schedule import schedule_bp
from dotenv import load_dotenv

# ----------------- Load Environment -----------------

load_dotenv()

# ----------------- Logging Setup -----------------

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("reelvo")

# ----------------- Flask App Setup -----------------

flask_app = Flask(__name__)
flask_app.secret_key = os.getenv("FLASK_SECRET_KEY", "demo_secret")

# Load SMTP settings into config
flask_app.config["SMTP_HOST"] = os.getenv("SMTP_HOST")
flask_app.config["SMTP_PORT"] = int(os.getenv("SMTP_PORT", 587))
flask_app.config["SMTP_USERNAME"] = os.getenv("SMTP_USERNAME")
flask_app.config["SMTP_PASSWORD"] = os.getenv("SMTP_PASSWORD")
flask_app.config["SMTP_SENDER_NAME"] = os.getenv("SMTP_SENDER_NAME", "Reelvo.ai")
flask_app.config["SMTP_USE_TLS"] = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

# Register blueprints
flask_app.register_blueprint(auth_bp)
flask_app.register_blueprint(dashboard_bp)
flask_app.register_blueprint(reels_bp)
flask_app.register_blueprint(progress_bp)
flask_app.register_blueprint(instagram_bp)
flask_app.register_blueprint(schedule_bp)

# ----------------- Background Threads -----------------

def start_background_tasks():
    Thread(target=refresh_instagram_tokens, daemon=True).start()
    Thread(target=scheduler_runner, daemon=True).start()

# ----------------- Start Server -----------------

def run():
    os.makedirs("output", exist_ok=True)
    start_background_tasks()

    port = int(os.getenv("PORT", 5000))
    host = os.getenv("HOST", "0.0.0.0")
    logger.info(f"🚀 Production server starting at http://{host}:{port}")

    # Development server (use_debugger=True is not for production)
    run_simple(host, port, flask_app, use_debugger=True, use_reloader=True)

    # Uncomment below for production use:
    # serve(flask_app, host=host, port=port)

if __name__ == "__main__":
    run()

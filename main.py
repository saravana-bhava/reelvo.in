# File: main.py

import os
import logging
from flask import Flask
from threading import Thread
from waitress import serve  # For production server

from utils.scheduler import scheduler_runner
from utils.instagram_token_refresher import refresh_instagram_tokens
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.reels import reels_bp
from routes.progress import progress_bp
from routes.instagram import instagram_bp
from routes.schedule import schedule_bp

# ----------------- Logging Setup -----------------

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("reelvo")

# ----------------- Flask App Setup -----------------

flask_app = Flask(__name__)
flask_app.secret_key = os.getenv("FLASK_SECRET_KEY", "demo_secret")

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

    serve(flask_app, host=host, port=port)  # Use Waitress instead of Flask dev server

if __name__ == "__main__":
    run()

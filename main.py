# File: main.py

import os
import logging
import time
from flask import Flask
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple
from threading import Thread

from utils.scheduler import scheduler_runner
from utils.instagram_token_refresher import refresh_instagram_tokens
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.reels import reels_bp
from routes.progress import progress_bp
from routes.instagram import instagram_bp
from routes.schedule import schedule_bp

# ----------------- App Setup -----------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("reelvo")

flask_app = Flask(__name__)
flask_app.secret_key = os.getenv("FLASK_SECRET_KEY", "demo_secret")

# Register blueprints
flask_app.register_blueprint(auth_bp)
flask_app.register_blueprint(dashboard_bp)
flask_app.register_blueprint(reels_bp)
flask_app.register_blueprint(progress_bp)
flask_app.register_blueprint(instagram_bp)
flask_app.register_blueprint(schedule_bp)

# ----------------- WSGI Setup -----------------

wsgi_app = DispatcherMiddleware(
    lambda environ, start_response: start_response("404 Not Found", []) or [b"404 Not Found"],
    {"/reelvo.ai": flask_app}
)

# ----------------- Start Server -----------------

if __name__ == "__main__":
    os.makedirs("output", exist_ok=True)
    Thread(target=refresh_instagram_tokens, daemon=True).start()
    Thread(target=scheduler_runner, daemon=True).start()
    port = int(os.getenv("PORT", 5000))
    logger.info(f"🚀 Dev server running at http://127.0.0.1:{port}/reelvo.ai")
    run_simple("127.0.0.1", port, wsgi_app, use_debugger=True, use_reloader=True)

# File: main.py

import os
import logging
from flask import Flask
from threading import Thread
from werkzeug.serving import run_simple
from werkzeug.middleware.proxy_fix import ProxyFix
from waitress import serve

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

# ✅ Trust proxy headers (especially for HTTPS on Render)
flask_app.wsgi_app = ProxyFix(flask_app.wsgi_app, x_proto=1, x_host=1)

# SMTP Configuration
flask_app.config.update(
    SMTP_HOST=os.getenv("SMTP_HOST"),
    SMTP_PORT=int(os.getenv("SMTP_PORT", 587)),
    SMTP_USERNAME=os.getenv("SMTP_USERNAME"),
    SMTP_PASSWORD=os.getenv("SMTP_PASSWORD"),
    SMTP_SENDER_NAME=os.getenv("SMTP_SENDER_NAME", "Reelvo.ai"),
    SMTP_USE_TLS=os.getenv("SMTP_USE_TLS", "true").lower() == "true"
)

# ----------------- Register Blueprints -----------------
flask_app.register_blueprint(auth_bp)
flask_app.register_blueprint(dashboard_bp)
flask_app.register_blueprint(reels_bp)
flask_app.register_blueprint(progress_bp)
flask_app.register_blueprint(instagram_bp)
flask_app.register_blueprint(schedule_bp)

# ----------------- Background Threads -----------------
def start_background_tasks():
    logger.info("Starting background tasks...")
    Thread(target=refresh_instagram_tokens, daemon=True).start()
    Thread(target=scheduler_runner, daemon=True).start()

# ----------------- Start Server -----------------
def run():
    os.makedirs("output", exist_ok=True)
    start_background_tasks()

    port = int(os.getenv("PORT", 5000))
    protocol = "http"
    host = "0.0.0.0"

    logger.info(f"🚀 Production server starting at {protocol}://{host}:{port}")

    if os.getenv("FLASK_ENV", "production").lower() == "development":
        logger.warning("⚠️ Running in development mode with debugger enabled!")
        run_simple(host, port, flask_app, use_debugger=True, use_reloader=True)
    else:
        # For production, prefer a WSGI server like Waitress or Gunicorn
        # To use Waitress, uncomment below:
        serve(flask_app, host=host, port=port)

if __name__ == "__main__":
    run()

from flask import redirect, url_for

@flask_app.route("/")
def index():
    return redirect(url_for("auth.login"))

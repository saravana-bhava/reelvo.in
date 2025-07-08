# File: main.py

import os
import logging
from threading import Thread

from flask import Flask
from werkzeug.serving import run_simple
from werkzeug.middleware.proxy_fix import ProxyFix
from waitress import serve
from dotenv import load_dotenv

from utils.scheduler import scheduler_runner
from utils.instagram_token_refresher import refresh_instagram_tokens
from routes.home import home_bp
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.reels import reels_bp
from routes.progress import progress_bp
from routes.instagram import instagram_bp
from routes.schedule import schedule_bp

# Load environment variables
load_dotenv()

# Logging setup
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("reelvo")

# Flask app initialization
flask_app = Flask(__name__)
flask_app.secret_key = os.getenv("FLASK_SECRET_KEY", "demo_secret")

# Enable proxy headers (important for HTTPS on reverse proxies like Cloudflare)
flask_app.wsgi_app = ProxyFix(flask_app.wsgi_app, x_proto=1, x_host=1)

# SMTP configuration
flask_app.config.update(
    SMTP_HOST=os.getenv("SMTP_HOST"),
    SMTP_PORT=int(os.getenv("SMTP_PORT", 587)),
    SMTP_USERNAME=os.getenv("SMTP_USERNAME"),
    SMTP_PASSWORD=os.getenv("SMTP_PASSWORD"),
    SMTP_SENDER_NAME=os.getenv("SMTP_SENDER_NAME", "Reelvo.ai"),
    SMTP_USE_TLS=os.getenv("SMTP_USE_TLS", "true").lower() == "true",
    PREFERRED_URL_SCHEME="https"
)

# Register Blueprints
for bp in [
    home_bp, auth_bp, dashboard_bp, reels_bp,
    progress_bp, instagram_bp, schedule_bp
]:
    flask_app.register_blueprint(bp)

# Background task starter
def start_background_tasks():
    logger.info("🔄 Starting background tasks...")
    Thread(
        target=refresh_instagram_tokens,
        daemon=True,
        name="InstagramTokenRefresher"
    ).start()
    Thread(
        target=scheduler_runner,
        daemon=True,
        name="SchedulerRunner"
    ).start()

# Application runner
def run():
    os.makedirs("output", exist_ok=True)
    start_background_tasks()

    port = int(os.getenv("PORT", 5000))
    host = "0.0.0.0"
    dev_mode = os.getenv("FLASK_ENV", "production").lower() == "development"

    logger.info(f"🚀 Starting server at http://{host}:{port} ({'Dev' if dev_mode else 'Prod'} Mode)")

    if dev_mode:
        logger.warning("⚠️ Running in development mode with debugger!")
        run_simple(host, port, flask_app, use_debugger=True, use_reloader=True)
    else:
        serve(flask_app, host=host, port=port)

if __name__ == "__main__":
    run()

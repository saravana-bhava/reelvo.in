# File: main.py

import os
import logging
from threading import Thread

from flask import Flask
from werkzeug.serving import run_simple
from werkzeug.middleware.proxy_fix import ProxyFix
from waitress import serve
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ─────────────────────────────────────────────
# LOGGING CONFIGURATION
# ─────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("reelvo")

# ─────────────────────────────────────────────
# FLASK INITIALIZATION
# ─────────────────────────────────────────────
flask_app = Flask(__name__)
flask_app.secret_key = os.getenv("FLASK_SECRET_KEY", "demo_secret")

dev_mode = os.getenv("FLASK_ENV", "production").lower() == "development"
if dev_mode:
    flask_app.config["TEMPLATES_AUTO_RELOAD"] = True
    flask_app.jinja_env.auto_reload = True

# Enable support for reverse proxy headers (e.g., Cloudflare, Nginx)
flask_app.wsgi_app = ProxyFix(flask_app.wsgi_app, x_proto=1, x_host=1)

# ─────────────────────────────────────────────
# SQLITE CONFIGURATION (Replacing JSON)
# ─────────────────────────────────────────────
from db.models import db  # Import after dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(BASE_DIR, "db", "reelvo.db")
os.makedirs(os.path.dirname(db_path), exist_ok=True)

flask_app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
flask_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(flask_app)

with flask_app.app_context():
    db.create_all()

# ─────────────────────────────────────────────
# SMTP CONFIGURATION
# ─────────────────────────────────────────────
flask_app.config.update(
    ADMIN_MASTER_PASSWORD=os.getenv("ADMIN_MASTER_PASSWORD"),
    SMTP_HOST=os.getenv("SMTP_HOST"),
    SMTP_PORT=int(os.getenv("SMTP_PORT", 587)),
    SMTP_USERNAME=os.getenv("SMTP_USERNAME"),
    SMTP_PASSWORD=os.getenv("SMTP_PASSWORD"),
    SMTP_SENDER_NAME=os.getenv("SMTP_SENDER_NAME", "Reelvo"),
    SMTP_USE_TLS=os.getenv("SMTP_USE_TLS", "true").lower() == "true",
    PREFERRED_URL_SCHEME="https"
)

# ─────────────────────────────────────────────
# REGISTER ROUTE BLUEPRINTS
# ─────────────────────────────────────────────
from routes.home import home_bp
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.profile import profile_bp
from routes.reels import reels_bp
from routes.progress import progress_bp
from routes.instagram import instagram_bp
from routes.schedule import schedule_bp
from routes.coming_soon import coming_bp

blueprints = [
    home_bp,
    auth_bp,
    dashboard_bp,
    profile_bp,
    reels_bp,
    progress_bp,
    instagram_bp,
    schedule_bp,
    coming_bp,
]

for bp in blueprints:
    flask_app.register_blueprint(bp)

# ─────────────────────────────────────────────
# BACKGROUND TASKS
# ─────────────────────────────────────────────
from utils.scheduler import scheduler_runner
from utils.instagram_token_refresher import refresh_instagram_tokens

def start_background_tasks():
    """Start background threads for scheduling and Instagram token refresh."""
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

# ─────────────────────────────────────────────
# APPLICATION RUNNER
# ─────────────────────────────────────────────
def run():
    """Main entry point for running the Flask app."""
    os.makedirs("output", exist_ok=True)
    start_background_tasks()

    port = int(os.getenv("PORT", 5000))
    host = "0.0.0.0"

    logger.info(f"🚀 Starting server at http://{host}:{port} ({'Dev' if dev_mode else 'Prod'} Mode)")

    if dev_mode:
        logger.warning("⚠️ Running in development mode with debugger and auto-reloader.")
        run_simple(host, port, flask_app, use_debugger=True, use_reloader=True)
    else:
        serve(flask_app, host=host, port=port)

# Expose the app globally for WSGI servers
app = flask_app

if __name__ == "__main__":
    run()

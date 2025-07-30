# ================================================
# File:         app.py
# Description:  Flask application entry point, initializes app and routes
# Framework:    Flask + TailwindCSS
# Version:      1.0.0
# Last Updated: 31 July 2025
# Author:       Saravana Bhava
# Author URL:   https://SazM.in
# ================================================

import os
import logging
from threading import Thread

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv

# Load environment variables from .env file
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
# CREATE FLASK APP FUNCTION
# ─────────────────────────────────────────────
def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "demo_secret")

    is_dev = os.getenv("FLASK_ENV", "production").lower() == "development"

    if is_dev:
        app.config["TEMPLATES_AUTO_RELOAD"] = True
        app.jinja_env.auto_reload = True

    # Reverse proxy support (e.g., Cloudflare, Nginx)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # ──────── Database: SQLite ────────
    from models import db
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(BASE_DIR, "db", "reelvo.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    if is_dev:
        with app.app_context():
            db.create_all()

    # ──────── SMTP Config ────────
    app.config.update(
        ADMIN_MASTER_PASSWORD=os.getenv("ADMIN_MASTER_PASSWORD"),
        SMTP_HOST=os.getenv("SMTP_HOST"),
        SMTP_PORT=int(os.getenv("SMTP_PORT", 587)),
        SMTP_USERNAME=os.getenv("SMTP_USERNAME"),
        SMTP_PASSWORD=os.getenv("SMTP_PASSWORD"),
        SMTP_SENDER_NAME=os.getenv("SMTP_SENDER_NAME", "Reelvo"),
        SMTP_USE_TLS=os.getenv("SMTP_USE_TLS", "true").lower() == "true",
        PREFERRED_URL_SCHEME="https"
    )

    # ──────── Register Blueprints ────────
    from routes.home import home_bp
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.profile import profile_bp
    from routes.reels import reels_bp
    from routes.instagram import instagram_bp
    from routes.schedule import schedule_bp
    from routes.coming_soon import coming_bp
    from routes.privacy import privacy_bp
    from routes.terms import terms_bp

    blueprints = [
        home_bp, auth_bp, dashboard_bp, profile_bp,
        reels_bp, instagram_bp, schedule_bp,
        coming_bp, privacy_bp, terms_bp
    ]

    for bp in blueprints:
        app.register_blueprint(bp)

    # ──────── Context Processor ────────
    @app.context_processor
    def inject_user_logo():
        from flask import session
        user = session.get("user", {})
        email = user.get("email", "")
        logo_real_path = f"output/{email}/watermark/logo.png" if email else ""
        logo_path = f"watermark/{email}/logo.png" if email else ""
        has_logo = os.path.exists(logo_real_path)
        return {
            "user_email": email,
            "logo_path": logo_path,
            "has_profile_pic": has_logo,
        }

    return app

# ─────────────────────────────────────────────
# BACKGROUND TASKS
# ─────────────────────────────────────────────
def start_background_tasks():
    """Start background threads for scheduling and Instagram token refresh."""
    from utils.scheduler import scheduler_runner
    from utils.instagram_token_refresher import refresh_instagram_tokens

    logger.info("🔄 Starting background tasks...")

    Thread(target=refresh_instagram_tokens, daemon=True, name="InstagramTokenRefresher").start()
    Thread(target=scheduler_runner, daemon=True, name="SchedulerRunner").start()

# ─────────────────────────────────────────────
# MAIN RUNNER
# ─────────────────────────────────────────────
def run():
    """Main entry point for running the Flask app."""
    os.makedirs("output", exist_ok=True)

    # Optional: enable background task runner in production
    if os.getenv("ENABLE_BG_TASKS", "false").lower() == "true":
        start_background_tasks()

    port = int(os.getenv("PORT", 5000))
    host = "0.0.0.0"
    is_dev = os.getenv("FLASK_ENV", "production").lower() == "development"

    logger.info(f"🚀 Starting server at http://{host}:{port} ({'Dev' if is_dev else 'Prod'} Mode)")

    if is_dev:
        from werkzeug.serving import run_simple
        logger.warning("⚠️ Running in development mode with debugger and auto-reloader.")
        run_simple(host, port, app, use_debugger=True, use_reloader=True)
    else:
        from waitress import serve
        serve(app, host=host, port=port)

# ─────────────────────────────────────────────
# CLI ENTRY POINT
# ─────────────────────────────────────────────
app = create_app()

if __name__ == "__main__":
    run()

# ================================================
# File:         routes/instagram.py
# Description:  Instagram connection, OAuth, media syncing
# Framework:    Flask + TailwindCSS
# Version:      1.0.0
# Last Updated: 31 July 2025
# Author:       Saravana Bhava
# Author URL:   https://SazM.in
# ================================================

import os
import requests
from datetime import timedelta, datetime
from flask import (
    Blueprint, request, redirect, session, flash,
    url_for, jsonify, current_app, send_from_directory
)
from utils.instagram_db import update_instagram_tokens, delete_instagram_token
from utils.instagram import post_to_instagram
from utils.auth_utils import get_user_id, get_user_email
from werkzeug.exceptions import Unauthorized

instagram_bp = Blueprint("instagram", __name__)

INSTAGRAM_APP_ID = os.getenv("FB_APP_ID", "")
INSTAGRAM_APP_SECRET = os.getenv("FB_APP_SECRET", "")
REDIRECT_URI = os.getenv(
    "FB_REDIRECT_URI",
    f"{os.getenv('PROTOCOL', 'https')}://{os.getenv('HOST', 'localhost')}/instagram/callback"
)
GRAPH_API_BASE = "https://graph.facebook.com/v19.0"


# --------------------------
# Helpers
# --------------------------

def safe_get(url, params=None, timeout=10):
    """Wrapper for GET requests with error handling and logging."""
    try:
        response = requests.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        current_app.logger.error(f"[HTTP GET] {url} failed: {e}")
        return None


def download_and_save_image(url, save_path):
    """Downloads an image from URL and saves to given path."""
    try:
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "wb") as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        return True
    except Exception as e:
        current_app.logger.error(f"[Download Image] {url} failed: {e}")
        return False


# --------------------------
# OAuth Connect
# --------------------------

@instagram_bp.route("/connect-instagram", methods=["GET"])
def connect_instagram():
    auth_url = (
        f"https://www.facebook.com/v19.0/dialog/oauth"
        f"?client_id={INSTAGRAM_APP_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope=pages_show_list,pages_read_engagement,pages_manage_metadata,"
        f"instagram_basic,instagram_content_publish,business_management"
        f"&auth_type=rerequest"
    )
    return redirect(auth_url)


# --------------------------
# OAuth Callback
# --------------------------

@instagram_bp.route("/instagram/callback", methods=["GET"])
def instagram_callback():
    code = request.args.get("code")
    if not code:
        flash("❌ Authorization failed. No code received.", "error")
        return redirect(url_for("dashboard.dashboard"))

    try:
        # Step 1: Exchange code for short-lived token
        token_data = safe_get(
            f"{GRAPH_API_BASE}/oauth/access_token",
            params={
                "client_id": INSTAGRAM_APP_ID,
                "client_secret": INSTAGRAM_APP_SECRET,
                "redirect_uri": REDIRECT_URI,
                "code": code,
            }
        )
        short_token = token_data.get("access_token") if token_data else None
        if not short_token:
            flash("❌ Failed to obtain short-lived token.", "error")
            return redirect(url_for("dashboard.dashboard"))

        # Step 2: Exchange for long-lived token
        long_data = safe_get(
            f"{GRAPH_API_BASE}/oauth/access_token",
            params={
                "grant_type": "fb_exchange_token",
                "client_id": INSTAGRAM_APP_ID,
                "client_secret": INSTAGRAM_APP_SECRET,
                "fb_exchange_token": short_token,
            }
        )
        long_token = long_data.get("access_token") if long_data else None
        expires_in = long_data.get("expires_in", 60 * 60 * 24 * 60)
        refresh_token = ""

        if not long_token:
            flash("❌ Failed to obtain long-lived token.", "error")
            return redirect(url_for("dashboard.dashboard"))

        # Step 3: Get Facebook Pages
        pages_data = safe_get(f"{GRAPH_API_BASE}/me/accounts", params={"access_token": long_token})
        pages = pages_data.get("data", []) if pages_data else []

        if not pages:
            # Fallback: Get owned pages from business account
            biz_data = safe_get(f"{GRAPH_API_BASE}/me/businesses", params={"access_token": long_token})
            for biz in (biz_data.get("data", []) if biz_data else []):
                owned = safe_get(f"{GRAPH_API_BASE}/{biz['id']}/owned_pages", params={"access_token": long_token})
                if owned and "data" in owned and owned["data"]:
                    pages = owned["data"]
                    break

        if not pages:
            flash("❌ No Facebook Pages found. Check admin permissions.", "error")
            return redirect(url_for("dashboard.dashboard"))

        page_id = pages[0].get("id")
        if not page_id:
            flash("❌ Missing Page ID.", "error")
            return redirect(url_for("dashboard.dashboard"))

        # Step 4: Get Instagram business account
        ig_data = safe_get(
            f"{GRAPH_API_BASE}/{page_id}",
            params={"fields": "instagram_business_account", "access_token": long_token}
        )
        ig_user_id = ig_data.get("instagram_business_account", {}).get("id") if ig_data else None
        if not ig_user_id:
            flash("❌ Instagram account not linked to Page.", "error")
            return redirect(url_for("dashboard.dashboard"))

        # Step 5: Get IG profile picture
        profile_data = safe_get(
            f"{GRAPH_API_BASE}/{ig_user_id}",
            params={"fields": "username,profile_picture_url", "access_token": long_token}
        )
        profile_url = profile_data.get("profile_picture_url") if profile_data else None

        # Step 6: Save tokens and picture
        user_id = get_user_id()
        user_email = get_user_email()

        if user_id:
            if profile_url and user_email:
                logo_path = f"output/{user_email}/watermark/logo.png"
                if download_and_save_image(profile_url, logo_path):
                    session["instagram_profile_picture"] = logo_path
                else:
                    session["instagram_profile_picture"] = None

            update_instagram_tokens(user_id, long_token, refresh_token, expires_in, ig_user_id)
            session["connected"] = True
            flash("✅ Instagram connected successfully!", "success")

    except Exception as e:
        current_app.logger.exception("[OAuth] Instagram callback error")
        flash(f"❌ Instagram connection failed. {e}", "error")

    return redirect(url_for("dashboard.dashboard"))


# --------------------------
# Disconnect Instagram
# --------------------------

@instagram_bp.route("/disconnect-instagram", methods=["POST"])
def disconnect_instagram():
    user_id = get_user_id()
    if not user_id:
        raise Unauthorized("User not logged in")

    try:
        delete_instagram_token(user_id)
    except Exception as e:
        current_app.logger.error(f"[Disconnect] Token deletion failed: {e}")

    session["connected"] = False
    session.pop("instagram_profile_picture", None)
    flash("ℹ️ Instagram disconnected.", "info")
    return redirect(url_for("dashboard.dashboard"))


# --------------------------
# API: Post Reel to Instagram
# --------------------------

@instagram_bp.route("/api/post-reel", methods=["POST"])
def api_post_reel():
    user_id = get_user_id()
    if not user_id:
        return jsonify({"error": "User not logged in"}), 401

    data = request.get_json()
    video_path = data.get("video_path")
    caption = data.get("caption", "")
    video_url = data.get("video_url")

    if not video_path or not video_url:
        return jsonify({"error": "Missing required fields: video_path or video_url"}), 400

    try:
        user_email = get_user_email()
        result_html = post_to_instagram(
            reel_id=data.get("reel_id", ""),
            video_path=video_path,
            caption=caption,
            user_email=user_email,
            video_url=video_url
        )
        return jsonify({"success": True, "message": result_html})
    except Exception:
        current_app.logger.exception("[Instagram] Reel post failed")
        return jsonify({"error": "Failed to post to Instagram"}), 500


# --------------------------
# Serve watermark image
# --------------------------

@instagram_bp.route("/watermark/<user_email>/logo.png")
def serve_watermark(user_email):
    return send_from_directory(os.path.join("output", user_email, "watermark"), "logo.png")

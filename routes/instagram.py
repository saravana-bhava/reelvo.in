# File: routes/instagram.py

from flask import Blueprint, request, redirect, session, flash, url_for, jsonify, current_app
from datetime import timedelta
import requests
import os

from utils.user_db import save_user_tokens, get_instagram_credentials, log_post
from utils.instagram import post_to_instagram

instagram_bp = Blueprint("instagram", __name__)

# Constants
INSTAGRAM_APP_ID = os.getenv("FB_APP_ID", "")
INSTAGRAM_APP_SECRET = os.getenv("FB_APP_SECRET", "")
REDIRECT_URI = os.getenv("FB_REDIRECT_URI", f"{os.getenv('PROTOCOL', 'https')}://{os.getenv('HOST', 'localhost')}/instagram/callback")
GRAPH_API_BASE = "https://graph.facebook.com/v19.0"

# Safe GET wrapper
def safe_get(url, params=None, timeout=10):
    try:
        response = requests.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        current_app.logger.error(f"[HTTP] GET {url} failed: {e}")
        return None

# Step 1: Start OAuth connection
@instagram_bp.route("/connect-instagram", methods=["GET"])
def connect_instagram():
    auth_url = (
        "https://www.facebook.com/v19.0/dialog/oauth"
        f"?client_id={INSTAGRAM_APP_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        "&scope=pages_show_list,pages_read_engagement,pages_manage_metadata,"
        "instagram_basic,instagram_content_publish,business_management"
        "&auth_type=rerequest"
    )
    return redirect(auth_url)

# Step 2: OAuth Callback
@instagram_bp.route("/instagram/callback", methods=["GET"])
def instagram_callback():
    code = request.args.get("code")
    if not code:
        flash("❌ Authorization failed. No code received.", "error")
        return redirect(url_for("dashboard.dashboard"))

    try:
        # Exchange code for short-lived token
        token_data = safe_get(
            f"{GRAPH_API_BASE}/oauth/access_token",
            params={
                "client_id": INSTAGRAM_APP_ID,
                "client_secret": INSTAGRAM_APP_SECRET,
                "redirect_uri": REDIRECT_URI,
                "code": code,
            },
            timeout=15
        )
        if not token_data or "access_token" not in token_data:
            flash("❌ Failed to get short-lived access token.", "error")
            return redirect(url_for("dashboard.dashboard"))

        short_access_token = token_data["access_token"]

        # Exchange for long-lived token
        long_data = safe_get(
            f"{GRAPH_API_BASE}/oauth/access_token",
            params={
                "grant_type": "fb_exchange_token",
                "client_id": INSTAGRAM_APP_ID,
                "client_secret": INSTAGRAM_APP_SECRET,
                "fb_exchange_token": short_access_token,
            },
            timeout=10
        )
        if not long_data or "access_token" not in long_data:
            flash("❌ Failed to get long-lived access token.", "error")
            return redirect(url_for("dashboard.dashboard"))

        long_access_token = long_data["access_token"]
        expires_in = long_data.get("expires_in", 60 * 60 * 24 * 60)  # default: 60 days

        # Get pages
        pages_json = safe_get(
            f"{GRAPH_API_BASE}/me/accounts",
            params={"access_token": long_access_token}
        )
        pages = pages_json.get("data", []) if pages_json else []

        # Fallback: try Business Manager
        if not pages:
            biz_json = safe_get(f"{GRAPH_API_BASE}/me/businesses", params={"access_token": long_access_token})
            businesses = biz_json.get("data", []) if biz_json else []

            for biz in businesses:
                biz_id = biz.get("id")
                if not biz_id:
                    continue
                owned_json = safe_get(
                    f"{GRAPH_API_BASE}/{biz_id}/owned_pages",
                    params={"access_token": long_access_token}
                )
                if owned_json and "data" in owned_json and owned_json["data"]:
                    pages = owned_json["data"]
                    break

        if not pages:
            flash("❌ No Facebook Pages found. Ensure you have admin rights.", "error")
            return redirect(url_for("dashboard.dashboard"))

        page_id = pages[0].get("id")
        if not page_id:
            flash("❌ Page ID missing from Facebook response.", "error")
            return redirect(url_for("dashboard.dashboard"))

        # Get IG business account
        ig_json = safe_get(
            f"{GRAPH_API_BASE}/{page_id}",
            params={"fields": "instagram_business_account", "access_token": long_access_token}
        )
        ig_account = ig_json.get("instagram_business_account", {}) if ig_json else {}
        ig_user_id = ig_account.get("id")

        if not ig_user_id:
            flash("❌ Instagram business account not linked to Page.", "error")
            return redirect(url_for("dashboard.dashboard"))

        # Save tokens
        user_email = session.get("user")
        if user_email:
            save_user_tokens(user_email, long_access_token, "", expires_in)
            session["connected"] = True
            flash("✅ Instagram account connected successfully!", "success")

    except Exception:
        current_app.logger.exception("[OAuth] Instagram callback failed.")
        flash("❌ Instagram connection failed. Please try again later.", "error")

    return redirect(url_for("dashboard.dashboard"))

# Disconnect Instagram
@instagram_bp.route("/disconnect-instagram", methods=["POST"])
def disconnect_instagram():
    user_email = session.get("user")
    if not user_email:
        return redirect(url_for("auth.index"))

    token_path = f"user_tokens/{user_email}.json"
    if os.path.exists(token_path):
        try:
            os.remove(token_path)
        except Exception as e:
            current_app.logger.error(f"[Disconnect] Failed to delete token file: {e}")

    session["connected"] = False
    flash("ℹ️ Instagram disconnected.", "info")
    return redirect(url_for("dashboard.dashboard"))

# API: Post a reel
@instagram_bp.route("/api/post-reel", methods=["POST"])
def api_post_reel():
    data = request.get_json()
    video_path = data.get("video_path")
    caption = data.get("caption", "")
    video_url = data.get("video_url")

    user_email = session.get("user")
    if not user_email:
        return jsonify({"error": "User not logged in"}), 401

    if not video_path or not video_url:
        return jsonify({"error": "Missing required fields: video_path or video_url"}), 400

    try:
        result_html = post_to_instagram(
            video_path=video_path,
            caption=caption,
            user_name=user_email,
            video_url=video_url
        )
        return jsonify({"success": True, "message": result_html})
    except Exception:
        current_app.logger.exception("[Instagram] Failed to post reel.")
        return jsonify({"error": "Failed to post to Instagram"}), 500

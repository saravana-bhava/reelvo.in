# File: routes/instagram.py

from flask import Blueprint, request, redirect, session, flash, url_for, jsonify
from datetime import datetime, timedelta
import requests
import os
from utils.user_db import save_user_tokens, get_instagram_credentials, log_post
from utils.instagram import post_to_instagram

instagram_bp = Blueprint("instagram", __name__)

INSTAGRAM_APP_ID = os.getenv("IG_APP_ID", "")
INSTAGRAM_APP_SECRET = os.getenv("IG_APP_SECRET", "")
REDIRECT_URI = os.getenv("IG_REDIRECT_URI", "https://reelvo-ai.dev.sazm.in/instagram/callback")

GRAPH_API_BASE = "https://graph.facebook.com/v19.0"


@instagram_bp.route("/connect-instagram", methods=["GET"])
def connect_instagram():
    """
    Redirects user to Instagram OAuth via Meta.
    """
    auth_url = (
        f"https://www.facebook.com/v19.0/dialog/oauth"
        f"?client_id={INSTAGRAM_APP_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope=instagram_basic,pages_show_list,instagram_content_publish,pages_read_engagement"
    )
    return redirect(auth_url)


@instagram_bp.route("/instagram/callback", methods=["GET"])
def instagram_callback():
    """
    Handles OAuth callback and saves long-lived tokens.
    """
    code = request.args.get("code")
    if not code:
        flash("❌ Authorization failed. No code received.", "error")
        return redirect(url_for("dashboard.dashboard"))

    try:
        # Step 1: Exchange code for short-lived access token
        token_res = requests.get(
            f"https://graph.facebook.com/v19.0/oauth/access_token",
            params={
                "client_id": INSTAGRAM_APP_ID,
                "client_secret": INSTAGRAM_APP_SECRET,
                "redirect_uri": REDIRECT_URI,
                "code": code,
            },
            timeout=15
        )
        token_res.raise_for_status()
        short_token_data = token_res.json()
        short_access_token = short_token_data.get("access_token")

        if not short_access_token:
            flash("❌ Failed to get short-lived access token.", "error")
            return redirect(url_for("dashboard.dashboard"))

        # Step 2: Exchange for long-lived token
        long_token_res = requests.get(
            "https://graph.facebook.com/v19.0/oauth/access_token",
            params={
                "grant_type": "fb_exchange_token",
                "client_id": INSTAGRAM_APP_ID,
                "client_secret": INSTAGRAM_APP_SECRET,
                "fb_exchange_token": short_access_token,
            },
            timeout=10
        )
        long_token_res.raise_for_status()
        long_token_data = long_token_res.json()
        long_access_token = long_token_data["access_token"]
        expires_in = long_token_data.get("expires_in", 60 * 60 * 24 * 60)  # default 60 days

        # Step 3: Get Facebook pages
        pages_res = requests.get(
            f"{GRAPH_API_BASE}/me/accounts",
            params={"access_token": long_access_token},
            timeout=10
        )
        pages_res.raise_for_status()
        pages = pages_res.json().get("data", [])
        if not pages:
            flash("❌ No Facebook Pages found.", "error")
            return redirect(url_for("dashboard.dashboard"))

        page_id = pages[0]["id"]

        # Step 4: Get Instagram business account linked to page
        ig_res = requests.get(
            f"{GRAPH_API_BASE}/{page_id}",
            params={"fields": "instagram_business_account", "access_token": long_access_token},
            timeout=10
        )
        ig_res.raise_for_status()
        ig_account = ig_res.json().get("instagram_business_account", {})
        ig_user_id = ig_account.get("id")

        if not ig_user_id:
            flash("❌ Instagram business account not linked to Page.", "error")
            return redirect(url_for("dashboard.dashboard"))

        # Step 5: Save to user_tokens
        username = session.get("user")
        if username:
            save_user_tokens(username, long_access_token, "", expires_in)

        session["connected"] = True
        flash("✅ Instagram account connected successfully!", "success")

    except Exception as e:
        print("[OAuth ERROR]", e)
        flash("❌ Instagram connection failed.", "error")

    return redirect(url_for("dashboard.dashboard"))


@instagram_bp.route("/disconnect-instagram", methods=["POST"])
def disconnect_instagram():
    """
    Clears user's Instagram token file.
    """
    username = session.get("user")
    if not username:
        return redirect(url_for("auth.index"))

    # Clear token file
    path = f"user_tokens/{username}.json"
    if os.path.exists(path):
        os.remove(path)

    session["connected"] = False
    flash("ℹ️ Instagram disconnected.", "info")
    return redirect(url_for("dashboard.dashboard"))


@instagram_bp.route("/api/post-reel", methods=["POST"])
def api_post_reel():
    """
    Posts a Reel via JSON API. Needs: video_path, caption, video_url.
    """
    data = request.get_json()
    video_path = data.get("video_path")
    caption = data.get("caption", "")
    video_url = data.get("video_url")

    username = session.get("user")
    if not username:
        return jsonify({"error": "User not logged in"}), 401

    if not video_path or not video_url:
        return jsonify({"error": "Missing video_path or video_url"}), 400

    try:
        result_html = post_to_instagram(
            video_path=video_path,
            caption=caption,
            username=username,
            video_url=video_url
        )
        return jsonify({"success": True, "message": result_html})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# File: routes/instagram.py

from flask import Blueprint, request, redirect, session, flash, url_for, jsonify
import os
import requests
from datetime import datetime, timedelta
from utils.instagram import (
    get_instagram_auth_url,
    exchange_code_for_token,
    get_user_ig_account_id,
    post_reel_to_instagram
)

instagram_bp = Blueprint("instagram", __name__)

@instagram_bp.route("/connect-instagram", methods=["GET"])
def connect_instagram():
    """Redirect user to Instagram OAuth URL."""
    auth_url = get_instagram_auth_url()
    return redirect(auth_url)


@instagram_bp.route("/instagram/callback", methods=["GET"])
def instagram_callback():
    """Handle OAuth callback from Instagram (Meta)."""
    code = request.args.get("code")
    if not code:
        flash("Authorization failed. No code received.", "error")
        return redirect(url_for("dashboard.dashboard"))

    try:
        token_data = exchange_code_for_token(code)
        session["access_token"] = token_data["access_token"]
        session["access_token_expires_at"] = (
            datetime.utcnow() + timedelta(seconds=token_data["expires_in"])
        ).isoformat()

        ig_user_id = get_user_ig_account_id(token_data["access_token"])
        session["ig_user_id"] = ig_user_id

        flash("Instagram account connected successfully!", "success")
    except Exception as e:
        print("Error during Instagram callback:", e)
        flash("Instagram connection failed.", "error")

    return redirect(url_for("dashboard.dashboard"))


@instagram_bp.route("/disconnect-instagram", methods=["POST"])
def disconnect_instagram():
    """Disconnect user's Instagram session."""
    session.pop("access_token", None)
    session.pop("access_token_expires_at", None)
    session.pop("ig_user_id", None)
    flash("Instagram disconnected.", "info")
    return redirect(url_for("dashboard.dashboard"))


@instagram_bp.route("/api/post-reel", methods=["POST"])
def api_post_reel():
    """Programmatically trigger reel posting via API."""
    data = request.get_json()
    video_path = data.get("video_path")
    caption = data.get("caption", "")

    access_token = session.get("access_token")
    ig_user_id = session.get("ig_user_id")

    if not access_token or not ig_user_id:
        return jsonify({"error": "Instagram not connected"}), 401

    try:
        result = post_reel_to_instagram(video_path, caption, access_token, ig_user_id)
        return jsonify({"success": True, "result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

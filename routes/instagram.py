# File: routes/instagram.py

from flask import Blueprint, request, redirect, session, flash, url_for, jsonify
from datetime import datetime, timedelta
import requests
import os
import traceback

from utils.user_db import save_user_tokens, get_instagram_credentials, log_post
from utils.instagram import post_to_instagram

instagram_bp = Blueprint("instagram", __name__)

INSTAGRAM_APP_ID = os.getenv("FB_APP_ID", "")
INSTAGRAM_APP_SECRET = os.getenv("FB_APP_SECRET", "")
REDIRECT_URI = os.getenv("FB_REDIRECT_URI", "https://reelvo-ai.dev.sazm.in/instagram/callback")

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
        f"&scope=pages_show_list,pages_read_engagement,pages_manage_metadata,"
        f"instagram_basic,instagram_content_publish,business_management"
        f"&auth_type=rerequest"
    )
    print("📌 DEBUG: Redirecting to Meta OAuth:", auth_url)
    return redirect(auth_url)


@instagram_bp.route("/instagram/callback", methods=["GET"])
def instagram_callback():
    """
    Handles OAuth callback and saves long-lived tokens.
    Includes fallback for Business Manager-owned Pages.
    """
    code = request.args.get("code")
    if not code:
        flash("❌ Authorization failed. No code received.", "error")
        return redirect(url_for("dashboard.dashboard"))

    try:
        # Step 1: Exchange code for short-lived token
        token_res = requests.get(
            f"{GRAPH_API_BASE}/oauth/access_token",
            params={
                "client_id": INSTAGRAM_APP_ID,
                "client_secret": INSTAGRAM_APP_SECRET,
                "redirect_uri": REDIRECT_URI,
                "code": code,
            },
            timeout=15
        )
        token_res.raise_for_status()
        token_data = token_res.json()
        print("📌 DEBUG: Short-lived token response:", token_data)
        short_access_token = token_data.get("access_token")

        if not short_access_token:
            flash("❌ Failed to get short-lived access token.", "error")
            return redirect(url_for("dashboard.dashboard"))

        # Step 2: Exchange for long-lived token
        long_token_res = requests.get(
            f"{GRAPH_API_BASE}/oauth/access_token",
            params={
                "grant_type": "fb_exchange_token",
                "client_id": INSTAGRAM_APP_ID,
                "client_secret": INSTAGRAM_APP_SECRET,
                "fb_exchange_token": short_access_token,
            },
            timeout=10
        )
        long_token_res.raise_for_status()
        long_data = long_token_res.json()
        print("📌 DEBUG: Long-lived token response:", long_data)
        long_access_token = long_data["access_token"]
        expires_in = long_data.get("expires_in", 60 * 60 * 24 * 60)

        # Step 3: Try getting Facebook Pages via /me/accounts
        pages_res = requests.get(
            f"{GRAPH_API_BASE}/me/accounts",
            params={"access_token": long_access_token},
            timeout=10
        )
        pages_res.raise_for_status()
        pages_json = pages_res.json()
        print("📌 DEBUG: /me/accounts response:", pages_json)
        pages = pages_json.get("data", [])

        # Step 3.1: If no pages, try via business-owned pages fallback
        if not pages:
            print("⚠️ No pages via /me/accounts. Trying Business Manager fallback...")

            biz_res = requests.get(
                f"{GRAPH_API_BASE}/me/businesses",
                params={"access_token": long_access_token},
                timeout=10
            )
            biz_res.raise_for_status()
            biz_json = biz_res.json()
            print("📌 DEBUG: /me/businesses response:", biz_json)

            businesses = biz_json.get("data", [])
            for biz in businesses:
                biz_id = biz.get("id")
                if not biz_id:
                    continue

                owned_res = requests.get(
                    f"{GRAPH_API_BASE}/{biz_id}/owned_pages",
                    params={"access_token": long_access_token},
                    timeout=10
                )
                owned_res.raise_for_status()
                owned_json = owned_res.json()
                print(f"📌 DEBUG: /{biz_id}/owned_pages response:", owned_json)

                if owned_json.get("data"):
                    pages = owned_json["data"]
                    break  # Stop after first business that has a page

        if not pages:
            flash("❌ No Facebook Pages found. Make sure you are an admin of the Page OR have full control via Business Manager.", "error")
            return redirect(url_for("dashboard.dashboard"))

        page_id = pages[0]["id"]
        print(f"📌 DEBUG: Using page_id: {page_id}")

        # Step 4: Get Instagram business account linked to page
        ig_res = requests.get(
            f"{GRAPH_API_BASE}/{page_id}",
            params={"fields": "instagram_business_account", "access_token": long_access_token},
            timeout=10
        )
        ig_res.raise_for_status()
        ig_json = ig_res.json()
        print("📌 DEBUG: Page IG account response:", ig_json)
        ig_account = ig_json.get("instagram_business_account", {})
        ig_user_id = ig_account.get("id")
        print("📌 DEBUG: IG user ID:", ig_user_id)

        if not ig_user_id:
            flash("❌ Instagram business account not linked to Page. Please link your IG Business account in Page settings.", "error")
            return redirect(url_for("dashboard.dashboard"))

        # Step 5: Save tokens
        user_name = session.get("user")
        if user_name:
            print(f"📌 DEBUG: Saving tokens for user: {user_name}")
            save_user_tokens(user_name, long_access_token, "", expires_in)
            session["connected"] = True
            flash("✅ Instagram account connected successfully!", "success")

    except Exception as e:
        print("[OAuth ERROR]", traceback.format_exc())
        flash("❌ Instagram connection failed.", "error")

    return redirect(url_for("dashboard.dashboard"))


@instagram_bp.route("/disconnect-instagram", methods=["POST"])
def disconnect_instagram():
    """
    Clears user's Instagram token file.
    """
    user_name = session.get("user")
    if not user_name:
        return redirect(url_for("auth.index"))

    token_path = f"user_tokens/{user_name}.json"
    if os.path.exists(token_path):
        print(f"📌 DEBUG: Removing token file: {token_path}")
        os.remove(token_path)

    session["connected"] = False
    flash("ℹ️ Instagram disconnected.", "info")
    return redirect(url_for("dashboard.dashboard"))


@instagram_bp.route("/api/post-reel", methods=["POST"])
def api_post_reel():
    """
    Posts a Reel via JSON API. Requires: video_path, caption, video_url.
    """
    data = request.get_json()
    print("📌 DEBUG: API request data:", data)
    video_path = data.get("video_path")
    caption = data.get("caption", "")
    video_url = data.get("video_url")

    user_name = session.get("user")
    if not user_name:
        return jsonify({"error": "User not logged in"}), 401

    if not video_path or not video_url:
        return jsonify({"error": "Missing video_path or video_url"}), 400

    try:
        result_html = post_to_instagram(
            video_path=video_path,
            caption=caption,
            user_name=user_name,
            video_url=video_url
        )
        print("📌 DEBUG: Post result:", result_html)
        return jsonify({"success": True, "message": result_html})
    except Exception as e:
        print("📌 DEBUG: Post error:", e)
        return jsonify({"error": str(e)}), 500

# File: auth/instagram_oauth.py

"""
Instagram OAuth Utility Module

Handles login URL generation, token exchange, and Facebook page retrieval
for Instagram Content Publishing.
"""

import os
import requests
import logging
from urllib.parse import urlencode
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Logger setup
logger = logging.getLogger("instagram_oauth")

# Facebook App Config
FB_APP_ID = os.getenv("FB_APP_ID")
FB_APP_SECRET = os.getenv("FB_APP_SECRET")
FB_REDIRECT_URI = os.getenv("FB_REDIRECT_URI")


def get_login_url() -> str:
    """
    Generate Facebook OAuth login URL.

    Returns:
        str: Full URL to redirect user for Instagram authorization.
    """
    params = {
        "client_id": FB_APP_ID,
        "redirect_uri": FB_REDIRECT_URI,
        "scope": "instagram_basic,pages_show_list,instagram_content_publish",
        "response_type": "code"
    }
    url = f"https://www.facebook.com/v19.0/dialog/oauth?{urlencode(params)}"
    logger.info(f"[🔗] Generated Facebook login URL")
    return url


def exchange_code_for_token(code: str) -> dict:
    """
    Exchange authorization code for access token.

    Args:
        code (str): OAuth code from Facebook redirect.

    Returns:
        dict: Access token details from Facebook.
    """
    url = "https://graph.facebook.com/v19.0/oauth/access_token"
    params = {
        "client_id": FB_APP_ID,
        "client_secret": FB_APP_SECRET,
        "redirect_uri": FB_REDIRECT_URI,
        "code": code
    }

    try:
        res = requests.get(url, params=params, timeout=10)
        res.raise_for_status()
        logger.info("[🔐] Successfully exchanged code for token")
        return res.json()  # Contains access_token, expires_in, token_type
    except requests.RequestException as e:
        logger.exception(f"[❌] Token exchange failed: {e}")
        raise


def get_user_pages(access_token: str) -> list:
    """
    Retrieve Facebook pages linked to the user.

    Args:
        access_token (str): User's access token.

    Returns:
        list: List of page dictionaries.
    """
    url = "https://graph.facebook.com/v19.0/me/accounts"

    try:
        res = requests.get(url, params={"access_token": access_token}, timeout=10)
        res.raise_for_status()
        pages = res.json().get("data", [])
        logger.info(f"[📄] Retrieved {len(pages)} user pages")
        return pages
    except requests.RequestException as e:
        logger.exception(f"[❌] Failed to fetch user pages: {e}")
        raise

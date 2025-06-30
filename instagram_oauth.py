# File: auth/instagram_oauth.py

import os
import requests
from urllib.parse import urlencode
from dotenv import load_dotenv

load_dotenv()

FB_APP_ID = os.getenv("FB_APP_ID")
FB_APP_SECRET = os.getenv("FB_APP_SECRET")
FB_REDIRECT_URI = os.getenv("FB_REDIRECT_URI")

def get_login_url():
    params = {
        "client_id": FB_APP_ID,
        "redirect_uri": FB_REDIRECT_URI,
        "scope": "instagram_basic,pages_show_list,instagram_content_publish",
        "response_type": "code"
    }
    return f"https://www.facebook.com/v19.0/dialog/oauth?{urlencode(params)}"

def exchange_code_for_token(code: str):
    url = "https://graph.facebook.com/v19.0/oauth/access_token"
    params = {
        "client_id": FB_APP_ID,
        "client_secret": FB_APP_SECRET,
        "redirect_uri": FB_REDIRECT_URI,
        "code": code
    }
    res = requests.get(url, params=params)
    res.raise_for_status()
    return res.json()  # access_token, expires_in

def get_user_pages(access_token: str):
    url = "https://graph.facebook.com/v19.0/me/accounts"
    res = requests.get(url, params={"access_token": access_token})
    res.raise_for_status()
    return res.json()["data"]  # list of pages

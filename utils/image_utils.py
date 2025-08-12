# ================================================
# File:         utils/image_utils.py
# Description:  Image utility functions
# Framework:    Flask + TailwindCSS
# Version:      1.0.0
# Last Updated: 12 August 2025
# Author:       Saravana Bhava
# Author URL:   https://SazM.in
# ================================================

import os
import requests
from flask import current_app

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

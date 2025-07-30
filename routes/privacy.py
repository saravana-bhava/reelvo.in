# ================================================
# File:         routes/privacy.py
# Description:  No description provided.
# Framework:    Flask + TailwindCSS
# Version:      1.0.0
# Last Updated: 31 July 2025
# Author:       Saravana Bhava
# Author URL:   https://SazM.in
# ================================================

from flask import Blueprint, render_template

privacy_bp = Blueprint("privacy", __name__)


@privacy_bp.route("/privacy")
def privacy():
    """
    Render the privacy policy page.
    """
    return render_template("privacy.html")

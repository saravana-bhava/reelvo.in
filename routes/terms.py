# ================================================
# File:         routes/terms.py
# Description:  No description provided.
# Framework:    Flask + TailwindCSS
# Version:      1.0.0
# Last Updated: 31 July 2025
# Author:       Saravana Bhava
# Author URL:   https://SazM.in
# ================================================

from flask import Blueprint, render_template

terms_bp = Blueprint("terms", __name__)

@terms_bp.route("/terms")
def terms():
    """
    Render the Terms and Conditions page.
    """
    return render_template("terms.html")

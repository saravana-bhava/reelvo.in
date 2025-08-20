# ================================================
# File:         routes/terms.py
# Description:  Terms and conditions route
# Framework:    Flask + TailwindCSS
# Version:      1.0.0
# Last Updated: 20 August 2025
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

# ================================================
# File:         routes/data_deletion.py
# Description:  Data Deletion route
# Framework:    Flask + TailwindCSS
# Version:      1.0.0
# Last Updated: 3 August 2025
# Author:       Saravana Bhava
# Author URL:   https://SazM.in
# ================================================

from flask import Blueprint, render_template

data_deletion_bp = Blueprint("data_deletion", __name__)

@data_deletion_bp.route("/data_deletion")
def data_deletion():
    """
    Render the Data Deletion page.
    """
    return render_template("data_deletion.html")

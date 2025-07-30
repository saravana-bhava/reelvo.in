# ================================================
# File:         routes/coming_soon.py
# Description:  No description provided.
# Framework:    Flask + TailwindCSS
# Version:      1.0.0
# Last Updated: 31 July 2025
# Author:       Saravana Bhava
# Author URL:   https://SazM.in
# ================================================

from flask import Blueprint, render_template, abort

coming_bp = Blueprint("coming_soon", __name__)

# Feature name mappings for display
FEATURES_MAP = {
    "analytics": "Analytics",
    "refer": "Refer & Earn",
    "upgrade": "Upgrade Plan"
}


@coming_bp.route("/coming-soon/<feature>")
def show_coming(feature: str):
    """
    Render a generic "Coming Soon" page for unimplemented features.

    Args:
        feature (str): URL param representing the feature key.

    Returns:
        str: Rendered HTML template with the display name of the feature.
    """
    display_name = FEATURES_MAP.get(feature.lower().strip())
    if not display_name:
        abort(404)

    return render_template("coming_soon.html", feature_name=display_name)

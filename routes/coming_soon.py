# File: routes/coming_soon.py

from flask import Blueprint, render_template

coming_bp = Blueprint("coming_soon", __name__)

# Feature name mappings for display
FEATURES_MAP = {
    "analytics": "Analytics",
    "refer": "Refer & Earn",
    "upgrade": "Upgrade Plan"
}

@coming_bp.route("/coming-soon/<feature>")
def show_coming(feature):
    """
    Show a 'coming soon' page for unfinished features.
    """
    feature_key = (feature or "").lower()
    display_name = FEATURES_MAP.get(feature_key, "Feature Coming Soon")
    return render_template("coming_soon.html", feature_name=display_name)

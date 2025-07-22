# File: routes/coming_soon.py

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
    feature_key = feature.lower().strip()
    display_name = FEATURES_MAP.get(feature_key)

    if not display_name:
        # Optional: Only allow known features to avoid misuse
        abort(404)

    return render_template("coming_soon.html", feature_name=display_name)

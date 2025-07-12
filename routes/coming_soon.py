# File: routes/coming_soon.py

from flask import Blueprint, render_template

coming_bp = Blueprint("coming_soon", __name__)

@coming_bp.route("/coming-soon/<feature>")
def show_coming(feature):
    features_map = {
        "analytics": "Analytics",
        "refer": "Refer & Earn",
        "upgrade": "Upgrade Plan"
    }
    display_name = features_map.get(feature.lower(), "Feature")
    return render_template("coming_soon.html", feature_name=display_name)

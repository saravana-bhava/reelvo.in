# File: routes/terms.py

from flask import Blueprint, render_template

terms_bp = Blueprint("terms", __name__)

@terms_bp.route("/terms")
def terms():
    return render_template("terms.html")

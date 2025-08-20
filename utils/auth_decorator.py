# ================================================
# File:         utils/auth_decorator.py
# Description:  Decorator for protecting routes
# Framework:    Flask + TailwindCSS
# Version:      1.0.0
# Last Updated: 20 August 2025
# Author:       Saravana Bhava
# Author URL:   https://SazM.in
# ================================================

from functools import wraps
from typing import Callable, Any
from flask import session, redirect, url_for, flash, Response


def login_required(f: Callable) -> Callable:
    """
    Flask decorator to ensure a user is logged in before accessing a route.

    If not logged in, redirects to login page with a warning flash message.
    """
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Response:
        if "user" not in session:
            flash("⚠️ Please log in to access this page.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated_function

# File: utils/auth_decorator.py

from functools import wraps
from typing import Callable, Any
from flask import session, redirect, url_for, flash, Response


def login_required(f: Callable) -> Callable:
    """
    Flask decorator to ensure a user is logged in before accessing a route.

    Redirects to the login page with a flash message if the user is not in session.
    """
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Response:
        if "user" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated_function

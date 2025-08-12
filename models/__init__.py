# ================================================
# File:         models/__init__.py
# Description:  Model package initializer
# Framework:    Flask + TailwindCSS
# Version:      1.0.0
# Last Updated: 12 August 2025
# Author:       Saravana Bhava
# Author URL:   https://SazM.in
# ================================================

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .user import User
from .reel import Reel
from .plan import Plan
from .theme import Theme
from .token import UserToken
from .schedule import Schedule
from .progress import ProgressTask
from .auto_post_plan import AutoPostPlan

__all__ = [
    "db",
    "User",
    "Reel",
    "Plan",
    "Theme",
    "UserToken",
    "Schedule",
    "ProgressTask",
    "AutoPostPlan"
]

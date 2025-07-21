# File: utils/reel_history.py

"""
Handles reading and writing reel history for users using SQLAlchemy ORM.
Stores script text, caption, permalink, and timestamp per user and reel.
"""

from typing import Dict, List, Optional
from db import db
from db.models import Reel
from datetime import datetime


def add_reel_to_history(
    user_email: str,
    filename: str,
    script: str,
    caption: Optional[str] = None,
    permalink: Optional[str] = None,
    timestamp: Optional[str] = None
) -> None:
    """Insert or update a reel in the user's reel history."""
    existing = Reel.query.filter_by(user_email=user_email, video=filename).first()
    if existing:
        existing.script = script.strip()
        existing.caption = caption or ""
        existing.permalink = permalink or ""
        existing.created_at = timestamp or datetime.utcnow()
    else:
        reel = Reel(
            user_email=user_email.strip(),
            video=filename.strip(),
            script=script.strip(),
            caption=caption or "",
            permalink=permalink or "",
            created_at=timestamp or datetime.utcnow(),
            posted=False
        )
        db.session.add(reel)
    db.session.commit()


def list_user_reels(user_email: str) -> List[str]:
    """List filenames of all reels for a user."""
    reels = Reel.query.filter_by(user_email=user_email.strip()).all()
    return [reel.video for reel in reels]


def get_user_script(user_email: str, filename: str) -> Optional[str]:
    """Return script text for a specific user's reel."""
    reel = Reel.query.filter_by(
        user_email=user_email.strip(),
        video=filename.strip()
    ).first()
    return reel.script if reel else None


def get_user_reel_data(user_email: str, filename: str) -> Optional[Dict[str, str]]:
    """Return all data associated with a specific user's reel."""
    reel = Reel.query.filter_by(
        user_email=user_email.strip(),
        video=filename.strip()
    ).first()

    if reel:
        return {
            "script": reel.script,
            "caption": reel.caption,
            "permalink": reel.permalink,
            "timestamp": reel.created_at.isoformat() if reel.created_at else ""
        }
    return None
